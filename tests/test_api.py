from fastapi.testclient import TestClient
import pytest

import main


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "test-key")
    monkeypatch.setattr(main, "RATE_LIMIT", 100)
    main.cache.clear()
    main.rate_counts.clear()


def client():
    return TestClient(main.app, headers={"Authorization": "Bearer test-key"})


def test_auth_rate_limit_and_health(monkeypatch):
    assert TestClient(main.app).get("/health").status_code == 200
    assert TestClient(main.app).get("/rating/atcoder/tourist").status_code == 401
    monkeypatch.setattr(main, "RATE_LIMIT", 1)
    monkeypatch.setattr(main.fetcher, "get_rating_by_platform", lambda p, u: {"status": "success", "rating": 42})
    assert client().get("/rating/atcoder/tourist").status_code == 200
    assert client().get("/rating/atcoder/tourist").status_code == 429


def test_single_errors_are_http_errors_and_never_cached(monkeypatch):
    calls = []

    def fetch(platform, username):
        calls.append(username)
        if username == "missing":
            return {"status": "user_not_found"}
        return {"status": "upstream_error"}

    monkeypatch.setattr(main.fetcher, "get_rating_by_platform", fetch)
    for _ in range(2):
        assert client().get("/rating/leetcode/missing").status_code == 404
        assert client().post("/rating", json={"platform": "leetcode", "username": "down"}).status_code == 502
    assert calls == ["missing", "down", "missing", "down"]
    assert not main.cache


def test_success_cache_and_batch(monkeypatch):
    calls = []

    def fetch(platform, username):
        calls.append((platform, username))
        return {"platform": platform, "username": username, "rating": 123, "status": "success"}

    monkeypatch.setattr(main.fetcher, "get_rating_by_platform", fetch)
    assert client().get("/rating/atcoder/tourist").json()["rating"] == 123
    assert client().get("/rating/atcoder/tourist").json()["rating"] == 123
    assert len(calls) == 1
    response = client().post("/ratings", json={"requests": [{"platform": "atcoder", "username": "tourist"}]})
    assert response.status_code == 200
    assert response.json()["successful_requests"] == 1
    assert client().post("/ratings", json={"requests": []}).status_code == 422
    assert client().get("/rating/unknown/user").status_code == 400
