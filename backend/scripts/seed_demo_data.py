from app.database import SessionLocal, init_db
from app.store import EtsyPulseStore


def main() -> None:
    init_db()
    with SessionLocal() as session:
        store = EtsyPulseStore(session)
        store.ensure_demo_seeded()
        print("Seeded deterministic demo shop, run, activity, debug events, and briefs.")


if __name__ == "__main__":
    main()
