from app.services.brightdata_client import BrightDataClient


def main() -> None:
    client = BrightDataClient(demo_mode=True)
    results = client.validate_demo_fixtures()
    for operation, summary in sorted(results.items()):
        print(f"{operation}: {summary}")


if __name__ == "__main__":
    main()
