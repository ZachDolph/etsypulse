from backend.scripts.smoke_openclaw_config import validate_files


def test_openclaw_config_files_validate() -> None:
    config = validate_files()

    assert config["bindings"] == []
    assert config["tools"]["agentToAgent"]["enabled"] is True
