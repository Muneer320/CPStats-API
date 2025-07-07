import requests
import time
from typing import Optional, Dict, Any
import json


class RatingFetcher:
    """Class to fetch ratings from various competitive programming platforms"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_leetcode_rating(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch LeetCode rating for a user"""
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

                result = {
                    'platform': 'leetcode',
                    'username': username,
                    'rating': contest_data['rating'] if contest_data else 0,
                    'global_ranking': contest_data['globalRanking'] if contest_data else None,
                    'contests_attended': contest_data['attendedContestsCount'] if contest_data else 0,
                    'profile_ranking': user_data['profile']['ranking'] if user_data.get('profile') else None,
                    'status': 'success'
                }
                return result
            else:
                return {
                    'platform': 'leetcode',
                    'username': username,
                    'rating': 0,
                    'status': 'user_not_found',
                    'error': 'User not found'
                }

        except Exception as e:
            return {
                'platform': 'leetcode',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_codeforces_rating(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch Codeforces rating for a user"""
        try:
            url = f"https://codeforces.com/api/user.info?handles={username}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data['status'] == 'OK' and data['result']:
                user_info = data['result'][0]
                return {
                    'platform': 'codeforces',
                    'username': username,
                    'rating': user_info.get('rating', 0),
                    'max_rating': user_info.get('maxRating', 0),
                    'rank': user_info.get('rank', 'unrated'),
                    'max_rank': user_info.get('maxRank', 'unrated'),
                    'contribution': user_info.get('contribution', 0),
                    'status': 'success'
                }
            else:
                return {
                    'platform': 'codeforces',
                    'username': username,
                    'rating': 0,
                    'status': 'user_not_found',
                    'error': 'User not found'
                }

        except Exception as e:
            return {
                'platform': 'codeforces',
                'username': username,
                'rating': 0,
                'status': 'error',
                'error': str(e)
            }

    def get_codechef_rating(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch CodeChef rating for a user"""
        try:
            url = f"https://www.codechef.com/users/{username}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Parse the HTML to extract rating information
            html_content = response.text

            # Look for rating in the HTML
            rating = 0
            max_rating = 0

            # Try to find rating using different patterns
            import re

            # Pattern for current rating
            rating_pattern = r'"rating":(\d+)'
            rating_match = re.search(rating_pattern, html_content)
            if rating_match:
                rating = int(rating_match.group(1))

            # Pattern for max rating
            max_rating_pattern = r'"highest_rating":(\d+)'
            max_rating_match = re.search(max_rating_pattern, html_content)
            if max_rating_match:
                max_rating = int(max_rating_match.group(1))

            # Check if user exists (if we found some data or if the page doesn't show 404)
            if "does not exist" in html_content.lower() or response.status_code == 404:
                return {
                    'platform': 'codechef',
                    'username': username,
                    'rating': 0,
                    'status': 'user_not_found',
                    'error': 'User not found'
                }

            return {
                'platform': 'codechef',
                'username': username,
                'rating': rating,
                'max_rating': max_rating,
                'status': 'success'
            }

        except Exception as e:
            return {
                'platform': 'codechef',
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
        results = []
        valid_ratings = []

        for request in requests_data:
            platform = request.get('platform', '').lower().strip()
            username = request.get('username', '').strip()

            if not platform or not username:
                results.append({
                    'platform': platform,
                    'username': username,
                    'rating': 0,
                    'status': 'error',
                    'error': 'Platform and username are required'
                })
                continue

            # Add small delay to avoid rate limiting
            time.sleep(0.5)

            rating_data = self.get_rating_by_platform(platform, username)
            results.append(rating_data)

            # Collect valid ratings for average calculation
            if rating_data['status'] == 'success' and rating_data['rating'] > 0:
                valid_ratings.append(rating_data['rating'])

        # Calculate average rating
        average_rating = sum(valid_ratings) / \
            len(valid_ratings) if valid_ratings else 0

        return {
            'results': results,
            'average_rating': round(average_rating, 2),
            'total_requests': len(requests_data),
            'successful_requests': len([r for r in results if r['status'] == 'success']),
            'valid_ratings_count': len(valid_ratings)
        }
