from app.core.power_profiles import (
    DEFAULT_PROFILE,
    PROFILE_CONFIGS,
    PowerProfile,
    get_profile_config,
)


def test_default_profile_is_balanced():
    assert DEFAULT_PROFILE == "BALANCED"


def test_all_profiles_registered():
    assert set(PROFILE_CONFIGS.keys()) == {p.value for p in PowerProfile}


def test_eco_budget_smallest():
    eco = PROFILE_CONFIGS["ECO"]
    balanced = PROFILE_CONFIGS["BALANCED"]
    performance = PROFILE_CONFIGS["PERFORMANCE"]
    assert eco.vram_budget_mb < balanced.vram_budget_mb < performance.vram_budget_mb


def test_eco_is_aggressive():
    assert PROFILE_CONFIGS["ECO"].aggressive_unload is True
    assert PROFILE_CONFIGS["BALANCED"].aggressive_unload is False
    assert PROFILE_CONFIGS["PERFORMANCE"].aggressive_unload is False


def test_get_profile_config_falls_back_to_balanced():
    config = get_profile_config("NOT_A_PROFILE")
    assert config is PROFILE_CONFIGS["BALANCED"]


def test_performance_has_longest_idle_timeout():
    eco = PROFILE_CONFIGS["ECO"]
    balanced = PROFILE_CONFIGS["BALANCED"]
    performance = PROFILE_CONFIGS["PERFORMANCE"]
    assert eco.idle_unload_seconds <= balanced.idle_unload_seconds <= performance.idle_unload_seconds
