from app.main import health


def test_health_handler() -> None:
    response = health()

    assert response.model_dump() == {
        "status": "ok",
        "service": "etsypulse-api",
        "demo_mode": True,
    }
