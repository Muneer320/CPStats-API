from unittest.mock import Mock

import rating_fetcher
import requests


def response(status, text="", json=None):
    result = Mock(status_code=status, text=text)
    result.raise_for_status.side_effect = requests.HTTPError("upstream HTTP error") if status >= 400 else None
    result.json.return_value = json
    return result


def test_atcoder_rank_is_read_from_contest_row(monkeypatch):
    html = """<table><tr><th>Rank</th><td>1st (Top &lt;0.01%)</td></tr>
    <tr><th>Rating</th><td>3,730</td></tr><tr><th>Highest Rating</th><td>4,229</td></tr></table>"""
    fetcher = rating_fetcher.RatingFetcher()
    monkeypatch.setattr(fetcher, "_get", lambda url: response(200, html))
    result = fetcher.get_rating_by_platform("atcoder", "tourist")
    assert (result["rank"], result["rating"], result["max_rating"]) == (1, 3730, 4229)


def test_codechef_ranks_and_unavailable_markup(monkeypatch):
    html = """<div class="rating-number">1,850</div><ul>
    <li>Global Rank 123</li><li>Country Rank 5</li></ul>"""
    fetcher = rating_fetcher.RatingFetcher()
    monkeypatch.setattr(fetcher, "_get", lambda url: response(200, html))
    result = fetcher.get_rating_by_platform("codechef", "example")
    assert (result["rating"], result["global_rank"], result["country_rank"]) == (1850, 123, 5)
    monkeypatch.setattr(fetcher, "_get", lambda url: response(403, "blocked"))
    blocked = fetcher.get_rating_by_platform("codechef", "example")
    assert blocked["status"] == "upstream_error"
    assert "rating" not in blocked


def test_leetcode_missing_user_is_not_a_zero_rating(monkeypatch):
    payload = {"data": {"matchedUser": None, "userContestRanking": None}}
    monkeypatch.setattr(rating_fetcher.requests, "post", lambda *a, **kw: response(200, json=payload))
    result = rating_fetcher.RatingFetcher().get_rating_by_platform("leetcode", "missing")
    assert result["status"] == "user_not_found"
    assert "rating" not in result
