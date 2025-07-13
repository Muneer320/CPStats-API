import requests
import time
import logging
import re
import json
from typing import Dict, Any
from bs4 import BeautifulSoup


class RatingFetcher:
    """Class to fetch ratings from various competitive programming platforms"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_leetcode_rating(self, username: str) -> Dict[str, Any]:
        """Fetch LeetCode rating for a user"""
        logger = logging.getLogger(__name__)
        logger.info(f"Fetching LeetCode rating for user: {username}")

        try:
            # GraphQL query for LeetCode
            url = "https://leetcode.com/graphql"
            query = """
            query getUserProfile($username: String!) {
                matchedUser(username: $username) {
                    username
                    profile {
                        ranking
                    }
                    submitStats {
                        acSubmissionNum {
                            difficulty
                            count
                        }
                    }
                }
                userContestRanking(username: $username) {
                    attendedContestsCount
                    rating
                    globalRanking
                    topPercentage
                }
            }
            """

            payload = {
                "query": query,
                "variables": {"username": username}
            }

            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('data') and data['data'].get('matchedUser'):
                user_data = data['data']['matchedUser']
                contest_data = data['data'].get('userContestRanking')

                rating = contest_data['rating'] if contest_data else 0
                logger.info(
                    f"Successfully fetched LeetCode data for {username}: rating={rating}")

                result = {
                    'platform': 'leetcode',
                    'username': username,
                    'rating': rating,
                    'global_ranking': contest_data['globalRanking'] if contest_data else None,
                    'contests_attended': contest_data['attendedContestsCount'] if contest_data else 0,
                    'profile_ranking': user_data['profile']['ranking'] if user_data.get('profile') else None,
                    'status': 'success'
                }
                return result
            else:
                logger.warning(f"LeetCode user not found: {username}")
                return {
                    'platform': 'leetcode',
                    'username': username,
                    'rating': 0,
                    'status': 'user_not_found',
                    'error': 'User not found'
                }

        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout while fetching LeetCode data for {username}")
            return {
                'platform': 'leetcode',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            logger.error(
                f"Connection error while fetching LeetCode data for {username}")
            return {
                'platform': 'leetcode',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Connection error'
            }
        except Exception as e:
            logger.error(
                f"Unexpected error fetching LeetCode data for {username}: {str(e)}")
            return {
                'platform': 'leetcode',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_codeforces_rating(self, username: str) -> Dict[str, Any]:
        """Fetch Codeforces rating for a user"""
        logger = logging.getLogger(__name__)
        logger.info(f"Fetching Codeforces rating for user: {username}")

        try:
            url = f"https://codeforces.com/api/user.info?handles={username}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data['status'] == 'OK' and data['result']:
                user_info = data['result'][0]
                rating = user_info.get('rating', 0)
                max_rating = user_info.get('maxRating', 0)

                logger.info(
                    f"Successfully fetched Codeforces data for {username}: rating={rating}, max_rating={max_rating}")

                return {
                    'platform': 'codeforces',
                    'username': username,
                    'rating': rating,
                    'max_rating': max_rating,
                    'rank': user_info.get('rank', 'unrated'),
                    'max_rank': user_info.get('maxRank', 'unrated'),
                    'contribution': user_info.get('contribution', 0),
                    'status': 'success'
                }
            else:
                logger.warning(f"Codeforces user not found: {username}")
                return {
                    'platform': 'codeforces',
                    'username': username,
                    'rating': 0,
                    'status': 'user_not_found',
                    'error': 'User not found'
                }

        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout while fetching Codeforces data for {username}")
            return {
                'platform': 'codeforces',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            logger.error(
                f"Connection error while fetching Codeforces data for {username}")
            return {
                'platform': 'codeforces',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Connection error'
            }
        except Exception as e:
            logger.error(
                f"Unexpected error fetching Codeforces data for {username}: {str(e)}")
            return {
                'platform': 'codeforces',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_codechef_rating(self, username: str) -> Dict[str, Any]:
        """Fetch CodeChef rating for a user"""
        logger = logging.getLogger(__name__)
        logger.info(f"Fetching CodeChef rating for user: {username}")

        try:
            url = f"https://www.codechef.com/users/{username}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Parse the HTML to extract rating information
            html_content = response.text

            # Check if user exists (404 or 'Page Not Found')
            if response.status_code == 404 or 'page not found' in html_content.lower():
                logger.warning(f"CodeChef user not found: {username}")
                return {
                    'platform': 'codechef',
                    'username': username,
                    'rating': 0,
                    'status': 'user_not_found',
                    'error': 'User not found'
                }

            soup = BeautifulSoup(html_content, 'html.parser')

            # Initialize defaults
            rating = 0
            max_rating = 0
            country_flag = ""
            country_name = ""
            global_rank = 0
            country_rank = 0
            stars = "unrated"

            # Find current rating
            rating_element = soup.select_one(".rating-number")
            if rating_element:
                rating_text = rating_element.get_text(strip=True)
                rating_digits = re.sub(r'[^\d]', '', rating_text)
                if rating_digits:
                    try:
                        rating = int(rating_digits)
                        logger.debug(
                            f"Successfully parsed current rating for {username}: {rating}")
                    except ValueError:
                        logger.warning(
                            f"Failed to parse rating digits for {username}: '{rating_digits}'")
                        rating = 0
                else:
                    logger.debug(
                        f"No rating digits found in text: '{rating_text}'")
            else:
                logger.debug(f"No rating-number element found for {username}")

            # Find max rating by traversing parent children
            if rating_element and rating_element.parent:
                try:
                    children = rating_element.parent.children
                    children_list = [
                        child for child in children if child != '\n']

                    if len(children_list) > 4:
                        max_rating_element = children_list[-1]
                        max_rating_text = max_rating_element.get_text(
                            strip=True)

                        if "Rating" in max_rating_text:
                            # Extract text after "Rating"
                            max_rating_part = max_rating_text.split("Rating")[
                                1].strip()
                            max_rating_digits = re.sub(
                                r'[^\d]', '', max_rating_part)

                            if max_rating_digits:
                                try:
                                    max_rating = int(max_rating_digits)
                                    logger.debug(
                                        f"Successfully parsed max rating for {username}: {max_rating}")
                                except ValueError:
                                    logger.warning(
                                        f"Failed to parse max rating digits for {username}: '{max_rating_digits}'")
                                    max_rating = 0
                            else:
                                logger.debug(
                                    f"No max rating digits found in text: '{max_rating_part}'")
                        else:
                            logger.debug(
                                f"'Rating' keyword not found in max rating text: '{max_rating_text}'")
                    else:
                        logger.debug(
                            f"Insufficient children elements for max rating parsing: {len(children_list)}")
                except Exception as e:
                    logger.debug(
                        f"Error parsing max rating structure for {username}: {e}")

            # Find country flag
            try:
                country_flag_element = soup.select_one(".user-country-flag")
                if country_flag_element:
                    country_flag = country_flag_element.get('src', '')
                    logger.debug(
                        f"Found country flag for {username}: {country_flag}")
            except Exception as e:
                logger.debug(f"Error parsing country flag for {username}: {e}")

            # Find country name
            try:
                country_name_element = soup.select_one(".user-country-name")
                if country_name_element:
                    country_name = country_name_element.get_text(strip=True)
                    logger.debug(
                        f"Found country name for {username}: {country_name}")
            except Exception as e:
                logger.debug(f"Error parsing country name for {username}: {e}")

            # Find global and country ranks
            try:
                from bs4 import Tag
                rating_ranks = soup.select_one(".rating-ranks")
                if rating_ranks:
                    ul_element = rating_ranks.find('ul')
                    if ul_element and isinstance(ul_element, Tag):
                        li_elements = ul_element.find_all('li')
                        for li in li_elements:
                            if isinstance(li, Tag):
                                li_text = li.get_text(strip=True)
                                if 'Global Rank' in li_text:
                                    global_rank_digits = re.sub(
                                        r'[^\d]', '', li_text)
                                    if global_rank_digits:
                                        try:
                                            global_rank = int(
                                                global_rank_digits)
                                            logger.debug(
                                                f"Found global rank for {username}: {global_rank}")
                                        except ValueError:
                                            logger.debug(
                                                f"Failed to parse global rank for {username}: '{global_rank_digits}'")
                                elif 'Country Rank' in li_text:
                                    country_rank_digits = re.sub(
                                        r'[^\d]', '', li_text)
                                    if country_rank_digits:
                                        try:
                                            country_rank = int(
                                                country_rank_digits)
                                            logger.debug(
                                                f"Found country rank for {username}: {country_rank}")
                                        except ValueError:
                                            logger.debug(
                                                f"Failed to parse country rank for {username}: '{country_rank_digits}'")
            except Exception as e:
                logger.debug(f"Error parsing ranks for {username}: {e}")

            # Find stars (rating category)
            try:
                stars_element = soup.select_one(".rating")
                if stars_element:
                    stars = stars_element.get_text(strip=True)
                    logger.debug(
                        f"Found stars/rating category for {username}: {stars}")
            except Exception as e:
                logger.debug(f"Error parsing stars for {username}: {e}")

            # Ensure max_rating is at least equal to current rating
            if max_rating < rating:
                logger.debug(
                    f"Max rating {max_rating} is less than current rating {rating}, setting max_rating = rating")
                max_rating = rating

            # Edge case: If no rating found at all
            if rating == 0 and max_rating == 0:
                logger.warning(
                    f"No rating information found for CodeChef user: {username}")

            logger.info(
                f"Successfully fetched CodeChef data for {username}: rating={rating}, max_rating={max_rating}, country={country_name}, global_rank={global_rank}")

            return {
                'platform': 'codechef',
                'username': username,
                'rating': rating,
                'max_rating': max_rating,
                'country_flag': country_flag,
                'country_name': country_name,
                'global_rank': global_rank,
                'country_rank': country_rank,
                'stars': stars,
                'status': 'success'
            }

        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout while fetching CodeChef data for {username}")
            return {
                'platform': 'codechef',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            logger.error(
                f"Connection error while fetching CodeChef data for {username}")
            return {
                'platform': 'codechef',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Connection error'
            }
        except Exception as e:
            logger.error(
                f"Unexpected error fetching CodeChef data for {username}: {str(e)}")
            return {
                'platform': 'codechef',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_atcoder_rating(self, username: str) -> Dict[str, Any]:
        """Fetch AtCoder rating for a user"""
        logger = logging.getLogger(__name__)
        logger.info(f"Fetching AtCoder rating for user: {username}")

        try:
            url = f"https://atcoder.jp/users/{username}"
            response = self.session.get(url, timeout=10)

            # Check if user exists (404 or page not found)
            if response.status_code == 404:
                logger.warning(f"AtCoder user not found: {username}")
                return {
                    'platform': 'atcoder',
                    'username': username,
                    'rating': 0,
                    'status': 'user_not_found',
                    'error': 'User not found'
                }

            response.raise_for_status()
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Initialize defaults
            rating = 0
            max_rating = 0
            rank = 0
            country = ""

            # Parse HTML table
            try:
                # Look for the rating in the user statistics table
                table_cells = soup.find_all(['td', 'th'])
                for i, cell in enumerate(table_cells):
                    cell_text = cell.get_text(strip=True)
                    if cell_text == "Rating":
                        # Rating value should be in the next cell
                        if i + 1 < len(table_cells):
                            rating_text = table_cells[i +
                                                      1].get_text(strip=True)
                            rating_digits = re.sub(
                                r'[^\d]', '', rating_text)
                            if rating_digits:
                                try:
                                    rating = int(rating_digits)
                                    logger.debug(
                                        f"Successfully parsed AtCoder rating from table for {username}: {rating}")
                                except ValueError:
                                    logger.debug(
                                        f"Failed to parse AtCoder rating from table for {username}: '{rating_text}'")
                        break

                    elif "Highest Rating" in cell_text:
                        if i + 1 < len(table_cells):
                            max_rating_text = table_cells[i +
                                                          1].get_text(strip=True)
                            max_rating_digits = re.sub(
                                r'[^\d]', '', max_rating_text)
                            if max_rating_digits:
                                try:
                                    max_rating = int(max_rating_digits)
                                    logger.debug(
                                        f"Successfully parsed AtCoder max rating from table for {username}: {max_rating}")
                                except ValueError:
                                    logger.debug(
                                        f"Failed to parse AtCoder max rating from table for {username}: '{max_rating_text}'")

                    elif "Rank" in cell_text:
                        print("rank found")
                        if i + 1 < len(table_cells):
                            rank_text = table_cells[i +
                                                    1].get_text(strip=True)
                            rank_text = re.sub(
                                r'[^\d]', '', rank_text)
                            if rank_text:
                                try:
                                    rank = int(rank_text)
                                    logger.debug(
                                        f"Successfully parsed AtCoder rank from table for {username}: {rank}")
                                except ValueError:
                                    logger.debug(
                                        f"Failed to parse AtCoder rank from table for {username}: '{rank_text}'")

            except Exception as e:
                logger.debug(
                    f"Error parsing AtCoder table for {username}: {e}")

            # Try to find country information
            try:
                table_cells = soup.find_all(['td', 'th'])
                for i, cell in enumerate(table_cells):
                    if "Country" in cell.get_text(strip=True):
                        if i + 1 < len(table_cells):
                            country = table_cells[i + 1].get_text(strip=True)
                            logger.debug(
                                f"Found AtCoder country for {username}: {country}")
                        break
            except Exception as e:
                logger.debug(
                    f"Error parsing AtCoder country for {username}: {e}")

            # Ensure max_rating is at least equal to current rating
            if max_rating < rating:
                max_rating = rating

            # Edge case: If no rating found at all
            if rating == 0 and max_rating == 0:
                logger.warning(
                    f"No rating information found for AtCoder user: {username}")

            logger.info(
                f"Successfully fetched AtCoder data for {username}: rating={rating}, max_rating={max_rating}, rank={rank}")

            return {
                'platform': 'atcoder',
                'username': username,
                'rating': rating,
                'max_rating': max_rating,
                'rank': rank,
                'country': country,
                'status': 'success'
            }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout while fetching AtCoder data for {username}")
            return {
                'platform': 'atcoder',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Request timeout'
            }
        except requests.exceptions.ConnectionError:
            logger.error(
                f"Connection error while fetching AtCoder data for {username}")
            return {
                'platform': 'atcoder',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': 'Connection error'
            }
        except Exception as e:
            logger.error(
                f"Unexpected error fetching AtCoder data for {username}: {str(e)}")
            return {
                'platform': 'atcoder',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_rating_by_platform(self, platform: str, username: str) -> Dict[str, Any]:
        """Get rating for a specific platform and username"""
        platform = platform.lower().strip()

        if platform == 'leetcode':
            return self.get_leetcode_rating(username)
        elif platform == 'codeforces':
            return self.get_codeforces_rating(username)
        elif platform == 'codechef':
            return self.get_codechef_rating(username)
        elif platform == 'atcoder':
            return self.get_atcoder_rating(username)
        else:
            return {
                'platform': platform,
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': f'Unsupported platform: {platform}'
            }

    def get_multiple_ratings(self, requests_data: list) -> Dict[str, Any]:
        """
        Get ratings for multiple platform/username pairs
        requests_data: List of dicts with 'platform' and 'username' keys
        """
        logger = logging.getLogger(__name__)
        logger.info(
            f"Fetching multiple ratings for {len(requests_data)} requests")

        results = []
        valid_ratings = []

        for i, request in enumerate(requests_data, 1):
            platform = request.get('platform', '').lower().strip()
            username = request.get('username', '').strip()

            if not platform or not username:
                logger.warning(
                    f"Request {i}: Missing platform or username - platform: '{platform}', username: '{username}'")
                results.append({
                    'platform': platform,
                    'username': username,
                    'rating': 0,
                    'status': 'error',
                    'error': 'Platform and username are required'
                })
                continue

            logger.debug(
                f"Processing request {i}/{len(requests_data)}: {platform}/{username}")

            # Add small delay to avoid rate limiting
            if i > 1:  # Don't delay on first request
                time.sleep(0.5)
                logger.debug(f"Applied rate limiting delay before request {i}")

            rating_data = self.get_rating_by_platform(platform, username)
            results.append(rating_data)

            # Collect valid ratings for average calculation
            if rating_data['status'] == 'success' and rating_data['rating'] > 0:
                valid_ratings.append(rating_data['rating'])

        # Calculate average rating
        average_rating = sum(valid_ratings) / \
            len(valid_ratings) if valid_ratings else 0
        successful_requests = len(
            [r for r in results if r['status'] == 'success'])

        logger.info(f"Completed multiple ratings fetch: {successful_requests}/{len(requests_data)} successful, "
                    f"average rating: {round(average_rating, 2)}")

        return {
            'results': results,
            'average_rating': round(average_rating, 2),
            'total_requests': len(requests_data),
            'successful_requests': successful_requests,
            'valid_ratings_count': len(valid_ratings)
        }
