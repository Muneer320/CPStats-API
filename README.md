---
title: CPStats API
emoji: 🏆
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
short_description: REST API for fetching CP ratings from multiple platforms
---

# CPStats API

[![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance REST API for fetching competitive programming ratings from multiple platforms including LeetCode, Codeforces, and CodeChef. Built with FastAPI and designed for production use.

## 🌟 Try the API

This Space is deployed and ready to use!

**🔗 Live API URL**: https://muneer320-cpstats-api.hf.space/

**⚠️ Authentication Required**: This API requires an API key for security. Contact the Space owner for access.

### Quick Test

Check if the API is running:

```bash
curl https://muneer320-cpstats-api.hf.space/health
```

Get supported platforms:

```bash
curl https://muneer320-cpstats-api.hf.space/platforms
```

### Using the API

All main endpoints require authentication with an API key:

```bash
curl -H "Authorization: Bearer your-api-key" \
     "https://muneer320-cpstats-api.hf.space/rating/codeforces/tourist"
```

## 🚀 Features

- **Multi-Platform Support**: LeetCode, Codeforces, and CodeChef
- **Batch Processing**: Handle multiple platform/username pairs in a single request
- **Rate Limiting**: Built-in request throttling and API protection
- **Caching**: Intelligent response caching to minimize external API calls
- **Authentication**: Secure API key-based authentication
- **Production Ready**: Docker support, health checks, and monitoring endpoints

## 📋 Supported Platforms

| Platform       | Data Retrieved                                    |
| -------------- | ------------------------------------------------- |
| **LeetCode**   | Contest rating, global ranking, contests attended |
| **Codeforces** | Current rating, max rating, rank, contribution    |
| **CodeChef**   | Current rating, highest rating                    |

## 🔗 Available Endpoints

### Public Endpoints

| Method | Endpoint     | Description                 |
| ------ | ------------ | --------------------------- |
| `GET`  | `/`          | API information and status  |
| `GET`  | `/health`    | Health check endpoint       |
| `GET`  | `/platforms` | List of supported platforms |

### Protected Endpoints (Require API Key)

| Method | Endpoint                            | Description                   |
| ------ | ----------------------------------- | ----------------------------- |
| `GET`  | `/rating/{platform}/{username}` | Get single user rating        |
| `POST` | `/rating`                       | Get single user rating (POST) |
| `POST` | `/ratings`                      | Get multiple user ratings     |

## 📖 Usage Examples

### Single Rating Query

```bash
curl -H "Authorization: Bearer your-api-key" \
     "https://muneer320-cpstats-api.hf.space/rating/codeforces/tourist"
```

**Response:**

```json
{
  "platform": "codeforces",
  "username": "tourist",
  "rating": 3726,
  "max_rating": 3979,
  "rank": "legendary grandmaster",
  "status": "success"
}
```

### Multiple Ratings Query

```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your-api-key" \
     -d '{
       "requests": [
         {"platform": "codeforces", "username": "tourist"},
         {"platform": "leetcode", "username": "jiangly"}
       ]
     }' \
     "https://muneer320-cpstats-api.hf.space/ratings"
```

**Response:**

```json
{
  "results": [
    {
      "platform": "codeforces",
      "username": "tourist",
      "rating": 3726,
      "max_rating": 3979,
      "rank": "legendary grandmaster",
      "status": "success"
    },
    {
      "platform": "leetcode",
      "username": "jiangly",
      "rating": 3400,
      "global_ranking": 15,
      "status": "success"
    }
  ],
  "average_rating": 3563.0,
  "total_requests": 2,
  "successful_requests": 2
}
```

### Testing Different Platforms

Try these examples with real usernames:

```bash
# Get Codeforces rating for tourist (legendary competitive programmer)
curl -H "Authorization: Bearer your-api-key" \
     "https://muneer320-cpstats-api.hf.space/rating/codeforces/tourist"

# Get LeetCode rating for a user
curl -H "Authorization: Bearer your-api-key" \
     "https://muneer320-cpstats-api.hf.space/rating/leetcode/jiangly"

# Get CodeChef rating
curl -H "Authorization: Bearer your-api-key" \
     "https://muneer320-cpstats-api.hf.space/rating/codechef/gennady"
```

### JavaScript/Web Integration

```javascript
const API_BASE = "https://muneer320-cpstats-api.hf.space";
const API_KEY = "your-api-key";

async function getUserRating(platform, username) {
  const response = await fetch(
    `${API_BASE}/rating/${platform}/${username}`,
    {
      headers: {
        Authorization: `Bearer ${API_KEY}`,
      },
    }
  );
  return await response.json();
}

// Usage
getUserRating("codeforces", "tourist").then((data) => {
  console.log(`${data.username} has rating ${data.rating} on ${data.platform}`);
});
```

### Python Integration

```python
import requests

API_BASE = 'https://muneer320-cpstats-api.hf.space'
API_KEY = 'your-api-key'

def get_user_rating(platform, username):
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(f'{API_BASE}/rating/{platform}/{username}', headers=headers)
    return response.json()

def get_multiple_ratings(requests_list):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {'requests': requests_list}
    response = requests.post(f'{API_BASE}/ratings', headers=headers, json=data)
    return response.json()

# Usage examples
rating = get_user_rating('codeforces', 'tourist')
print(f"Tourist's Codeforces rating: {rating['rating']}")

# Batch request
batch_request = [
    {'platform': 'codeforces', 'username': 'tourist'},
    {'platform': 'leetcode', 'username': 'jiangly'},
    {'platform': 'codechef', 'username': 'gennady'}
]
results = get_multiple_ratings(batch_request)
print(f"Average rating: {results['average_rating']}")
```

## 🔧 Use Cases

This API was originally built to power Discord bots that track competitive programming leaderboards, but can be used for:

- **Discord Bots**: Create ranking systems and leaderboards
- **Web Applications**: Build CP tracking dashboards
- **Mobile Apps**: Integrate CP ratings into mobile applications
- **Analytics**: Analyze competitive programming performance trends
- **Automated Systems**: Monitor rating changes and send notifications

## 📊 Monitoring

### Health Check

The API includes comprehensive health monitoring:

```bash
curl https://muneer320-cpstats-api.hf.space/health
```

Returns system status, cache information, and rate limiting details.

## 🛡️ Security Features

- **API Key Authentication**: Secure access control
- **Rate Limiting**: Prevent abuse and overuse (100 requests/hour by default)
- **CORS Configuration**: Control cross-origin requests
- **Input Validation**: Sanitize and validate all inputs
- **Error Handling**: Graceful error responses

## 🔧 Local Development

To run this API locally:

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Set environment variables**: Copy `.env.example` to `.env` and configure
4. **Generate API key**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
5. **Run**: `python main.py`

## 📜 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This API fetches data from public platforms and respects their rate limits. Users are responsible for complying with the terms of service of the respective platforms.

---

**Built with ❤️ for the competitive programming community**
