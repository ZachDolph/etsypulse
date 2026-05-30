from app.config import get_settings
from app.main import health, readiness


def test_health_handler(monkeypatch) -> None:
    monkeypatch.delenv("DEMO_MODE", raising=False)
    get_settings.cache_clear()
    import app.main as main_module
    main_module.settings = get_settings()

    response = health()

    assert response.model_dump() == {
        "status": "ok",
        "service": "etsypulse-api",
        "demo_mode": True,
    }


def test_readiness_handler_checks_database(monkeypatch) -> None:
    monkeypatch.delenv("DEMO_MODE", raising=False)
    get_settings.cache_clear()
    import app.main as main_module
    main_module.settings = get_settings()

    response = readiness()

    assert response.status == "ok"
    assert response.database == "ok"
    assert response.service == "etsypulse-api"
