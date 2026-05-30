import argparse
import sys

from app.config import deployment_warnings, get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EtsyPulse deployment environment without printing secrets.")
    parser.add_argument("--live", action="store_true", help="Require live Bright Data and LLM provider configuration.")
    parser.add_argument("--production", action="store_true", help="Apply production deployment checks.")
    args = parser.parse_args()

    get_settings.cache_clear()
    settings = get_settings()
    warnings = deployment_warnings(settings)
    errors: list[str] = []

    if args.production and settings.database_url.startswith("sqlite"):
        errors.append("DATABASE_URL must point at hosted Postgres for production deployment.")
    if args.production and not settings.cors_origins:
        errors.append("CORS_ORIGINS must include the deployed frontend URL.")
    if args.live and not settings.brightdata_live_ready:
        errors.append("Live validation requires BRIGHTDATA_API_KEY and BRIGHTDATA_UNLOCKER_ZONE.")
    if args.live and not settings.llm_live_ready:
        errors.append("Live validation requires NVIDIA_NIM_* or OPENROUTER_* configuration.")

    print(f"app_env={settings.app_env}")
    print(f"demo_mode={settings.demo_mode}")
    print(f"database={'postgres' if settings.database_url.startswith(('postgresql', 'postgres')) else 'sqlite_or_other'}")
    print(f"cors_origins_count={len(settings.cors_origins)}")
    print(f"brightdata_live_ready={settings.brightdata_live_ready}")
    print(f"llm_live_ready={settings.llm_live_ready}")

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
