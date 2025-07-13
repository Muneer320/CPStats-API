"""Scheduled smoke check against the two sources accessible in development."""

from rating_fetcher import RatingFetcher


def main():
    fetcher = RatingFetcher()
    for platform in ("atcoder", "codeforces"):
        result = fetcher.get_rating_by_platform(platform, "tourist")
        assert result["status"] == "success", (platform, result)
        assert isinstance(result["rating"], int) and result["rating"] > 0, result
        print(platform, "lookup succeeded")


if __name__ == "__main__":
    main()
