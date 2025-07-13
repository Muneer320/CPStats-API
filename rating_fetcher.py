"""Best-effort lookups for public competitive programming profiles."""

import logging
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "CPStats-API/1.1 (public profile lookup)"}
PLATFORMS = ("leetcode", "codeforces", "codechef", "atcoder")


def number(value):
    match = re.search(r"\d[\d,]*", value or "")
    return int(match.group().replace(",", "")) if match else None


def failure(platform, username, status, message):
    return {"platform": platform, "username": username, "status": status, "error": message}


def labeled_value(soup, label):
    for row in soup.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) >= 2 and cells[0].get_text(" ", strip=True).rstrip(":") == label:
            return cells[1].get_text(" ", strip=True)
    return None


def codechef_rank(soup, label):
    for item in soup.select("li, tr, p, div"):
        value = item.get_text(" ", strip=True)
        if re.fullmatch(rf"{re.escape(label)}\s*[:#]?\s*[\d,]+", value, re.I):
            return number(value[len(label):])
    return None


class RatingFetcher:
    def __init__(self, timeout=10):
        self.timeout = timeout

    def _get(self, url):
        return requests.get(url, headers=HEADERS, timeout=self.timeout)

    def get_leetcode_rating(self, username):
        query = """query profile($username: String!) {
          matchedUser(username: $username) { username profile { ranking } }
          userContestRanking(username: $username) {
            attendedContestsCount rating globalRanking topPercentage
          }
        }"""
        response = requests.post("https://leetcode.com/graphql", headers=HEADERS,
                                 json={"query": query, "variables": {"username": username}},
                                 timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise ValueError(f"LeetCode returned a GraphQL error: {payload['errors'][0].get('message', '')}")
        data = payload.get("data") or {}
        user = data.get("matchedUser")
        if not user:
            return failure("leetcode", username, "user_not_found", "User not found")
        contest = data.get("userContestRanking") or {}
        return {"platform": "leetcode", "username": username,
                "rating": contest.get("rating"), "global_ranking": contest.get("globalRanking"),
                "contests_attended": contest.get("attendedContestsCount", 0),
                "profile_ranking": (user.get("profile") or {}).get("ranking"), "status": "success"}

    def get_codeforces_rating(self, username):
        response = self._get(f"https://codeforces.com/api/user.info?handles={quote(username, safe='')}")
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "OK" or not data.get("result"):
            if data.get("status") == "FAILED" and "not found" in data.get("comment", "").lower():
                return failure("codeforces", username, "user_not_found", "User not found")
            raise ValueError("Codeforces returned an invalid response")
        user = data["result"][0]
        return {"platform": "codeforces", "username": username,
                "rating": user.get("rating"), "max_rating": user.get("maxRating"),
                "rank": user.get("rank", "unrated"), "max_rank": user.get("maxRank", "unrated"),
                "contribution": user.get("contribution"), "status": "success"}

    def get_codechef_rating(self, username):
        response = self._get(f"https://www.codechef.com/users/{quote(username, safe='')}")
        if response.status_code == 404:
            return failure("codechef", username, "user_not_found", "User not found")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rating_node = soup.select_one(".rating-number")
        if rating_node is None or number(rating_node.get_text(" ", strip=True)) is None:
            raise ValueError("CodeChef rating markup was not found")
        header = soup.select_one(".rating-header")
        highest = re.search(r"Highest\s+Rating\s*[:]?\s*([\d,]+)",
                            header.get_text(" ", strip=True) if header else "", re.I)
        country = soup.select_one(".user-country-name")
        stars = soup.select_one(".rating-star") or soup.select_one(".rating")
        return {"platform": "codechef", "username": username,
                "rating": number(rating_node.get_text(" ", strip=True)),
                "max_rating": number(highest.group(1)) if highest else None,
                "global_rank": codechef_rank(soup, "Global Rank"),
                "country_rank": codechef_rank(soup, "Country Rank"),
                "country_name": country.get_text(" ", strip=True) if country else None,
                "stars": stars.get_text(" ", strip=True) if stars else None,
                "status": "success"}

    def get_atcoder_rating(self, username):
        response = self._get(f"https://atcoder.jp/users/{quote(username, safe='')}")
        if response.status_code == 404:
            return failure("atcoder", username, "user_not_found", "User not found")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rank_text, rating_text = labeled_value(soup, "Rank"), labeled_value(soup, "Rating")
        if rank_text is None and rating_text is None:
            raise ValueError("AtCoder contest status markup was not found")
        return {"platform": "atcoder", "username": username,
                "rating": number(rating_text), "max_rating": number(labeled_value(soup, "Highest Rating")),
                "rank": number(rank_text), "country": labeled_value(soup, "Country/Region"),
                "status": "success"}

    def get_rating_by_platform(self, platform, username):
        platform, username = platform.lower().strip(), username.strip()
        if platform not in PLATFORMS:
            return failure(platform, username, "invalid_platform", "Unsupported platform")
        if not username or len(username) > 64:
            return failure(platform, username, "invalid_username", "Invalid username")
        try:
            return getattr(self, f"get_{platform}_rating")(username)
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            logger.warning("%s lookup failed for %s: %s", platform, username, exc)
            return failure(platform, username, "upstream_error", "Platform lookup failed")

    def get_multiple_ratings(self, requests_data):
        results = [self.get_rating_by_platform(item["platform"], item["username"])
                   for item in requests_data]
        return {"results": results, "total_requests": len(results),
                "successful_requests": sum(item["status"] == "success" for item in results)}
