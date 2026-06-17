import pytest

from phantom_quant.cli import _STRATEGIES
from phantom_quant.registry import (
    StrategyError,
    StrategyRegistry,
    StrategySpec,
    default_registry,
    load_strategy,
)
from phantom_quant.strategy import Strategy


def test_every_builtin_is_resolvable_by_current_name():
    for name in default_registry.list():
        assert isinstance(load_strategy(name), Strategy)


def test_registry_matches_cli_strategy_dict():
    for name, cls in _STRATEGIES.items():
        spec = StrategySpec(name, {"short": 3, "long": 6, "qty": 1000})

        from_registry = load_strategy(spec)
        from_cli_dict = cls(short=3, long=6, qty=1000)

        assert isinstance(from_registry, cls)
        assert (from_registry.short, from_registry.long, from_registry.qty) == (
            from_cli_dict.short,
            from_cli_dict.long,
            from_cli_dict.qty,
        )


def test_unknown_name_raises_strategy_error_with_choices():
    with pytest.raises(
        StrategyError,
        match=r"unknown strategy: does_not_exist\. choices: \['sma_cross'\]",
    ):
        load_strategy("does_not_exist")


def test_invalid_params_are_wrapped_as_strategy_error():
    spec = StrategySpec("sma_cross", {"short": 20, "long": 5})

    with pytest.raises(StrategyError, match="invalid params for sma_cross"):
        default_registry.from_config(spec)


def test_list_returns_builtins():
    assert "sma_cross" in default_registry.list()


def test_duplicate_register_raises_strategy_error():
    registry = StrategyRegistry()
    registry.register("sma_cross", _STRATEGIES["sma_cross"])

    with pytest.raises(StrategyError, match="duplicate strategy: sma_cross"):
        registry.register("sma_cross", _STRATEGIES["sma_cross"])
