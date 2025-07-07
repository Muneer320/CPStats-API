# CP Leaderboard API

[![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-performance REST API for fetching competitive programming ratings from multiple platforms including LeetCode, Codeforces, and CodeChef. Built with FastAPI for my Discord Bot.

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

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd cp-leaderboard-api
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Generate API key**

   ```python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Start the server**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once deployed, access the interactive API documentation at:

- `/docs` - Swagger UI (when DEBUG=True)
- `/redoc` - ReDoc interface (when DEBUG=True)

## 🔗 Endpoints

### Public Endpoints

| Method | Endpoint     | Description                 |
| ------ | ------------ | --------------------------- |
| `GET`  | `/`          | API information and status  |
| `GET`  | `/health`    | Health check endpoint       |
| `GET`  | `/platforms` | List of supported platforms |

### Protected Endpoints (Require API Key)

| Method | Endpoint                        | Description                   |
| ------ | ------------------------------- | ----------------------------- |
| `GET`  | `/rating/{platform}/{username}` | Get single user rating        |
| `POST` | `/rating`                       | Get single user rating (POST) |
| `POST` | `/ratings`                      | Get multiple user ratings     |

## 🔐 Authentication

All protected endpoints require an API key in the Authorization header:

```bash
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/rating/codeforces/username
```

## 📖 Usage Examples

### Single Rating Query

```bash
curl -H "Authorization: Bearer your-api-key" \
     "http://localhost:8000/rating/codeforces/tourist"
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
         {"platform": "leetcode", "username": "user123"}
       ]
     }' \
     "http://localhost:8000/ratings"
```

**Response:**

```json
{
  "results": [
    {
      "platform": "codeforces",
      "username": "tourist",
      "rating": 3726,
      "status": "success"
    },
    {
      "platform": "leetcode",
      "username": "user123",
      "rating": 2400,
      "status": "success"
    }
  ],
  "average_rating": 3063.0,
  "total_requests": 2,
  "successful_requests": 2
}
```

## ⚙️ Configuration

Configure the API using environment variables in `.env`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# Security
API_KEY=your-secret-api-key-here

# CORS (comma-separated)
ALLOWED_ORIGINS=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# Caching
ENABLE_CACHE=True
CACHE_TTL=300
```

## 🐳 Docker Deployment

### Using Docker

```bash
# Build image
docker build -t cp-leaderboard-api .

# Run container
docker run -p 8000:8000 --env-file .env cp-leaderboard-api
```

### Using Docker Compose

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
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

```bash
curl http://localhost:8000/health
```

### Rate Limiting

- Default: 100 requests per hour per API key
- Configurable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`
- Returns `429 Too Many Requests` when exceeded

### Caching

- Responses cached for 5 minutes by default
- Reduces load on external APIs
- Configurable via `CACHE_TTL`

## 🛡️ Security Features

- **API Key Authentication**: Secure access control
- **Rate Limiting**: Prevent abuse and overuse
- **CORS Configuration**: Control cross-origin requests
- **Input Validation**: Sanitize and validate all inputs
- **Error Handling**: Graceful error responses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This API fetches data from public platforms and respects their rate limits. Users are responsible for complying with the terms of service of the respective platforms.

## 🆘 Support

If you encounter issues:

1. Check the health endpoint: `/health`
2. Verify your API key and environment configuration
3. Review the logs for error details
4. Open an issue on GitHub with detailed information

---

**Built with ❤️ for the competitive programming community**
