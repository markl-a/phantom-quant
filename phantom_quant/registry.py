"""Loadable strategy registry.

DESIGN: This registry is ADDITIVE. It wraps the builtin strategy dict pattern;
builtins self-register into a default registry at import, and CLI behavior is
unchanged because ``phantom_quant.cli`` still owns its hardcoded mapping.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .strategies.sma_cross import SmaCross
from .strategy import Strategy


@dataclass(frozen=True)
class StrategySpec:
    name: str
    params: dict = field(default_factory=dict)


class StrategyError(Exception):
    """Raised when strategy lookup or creation fails."""


StrategyFactory = Callable[..., Strategy]


class StrategyRegistry:
    def __init__(self):
        self._factories: dict[str, StrategyFactory] = {}

    def register(self, name: str, factory: StrategyFactory) -> None:
        if name in self._factories:
            raise StrategyError(f"duplicate strategy: {name}")
        self._factories[name] = factory

    def get(self, name: str) -> StrategyFactory:
        try:
            return self._factories[name]
        except KeyError as exc:
            raise StrategyError(
                f"unknown strategy: {name}. choices: {self.list()}"
            ) from exc

    def list(self) -> list[str]:
        return sorted(self._factories)

    def from_config(self, spec: StrategySpec) -> Strategy:
        return self.create(spec.name, **spec.params)

    def create(self, name: str, **params) -> Strategy:
        factory = self.get(name)
        try:
            return factory(**params)
        except (TypeError, ValueError) as exc:
            raise StrategyError(f"invalid params for {name}: {exc}") from exc


default_registry = StrategyRegistry()
default_registry.register("sma_cross", SmaCross)


def load_strategy(
    spec_or_name: StrategySpec | str,
    registry: StrategyRegistry | None = None,
    **params,
) -> Strategy:
    """Resolve a typed StrategySpec OR a plain name (+**params) to a concrete Strategy via the registry (default: default_registry)."""
    selected_registry = default_registry if registry is None else registry
    if isinstance(spec_or_name, StrategySpec):
        return selected_registry.from_config(spec_or_name)
    return selected_registry.create(spec_or_name, **params)
