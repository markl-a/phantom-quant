"""End-to-end proof that paper trading and the registry are reachable from the
REAL CLI (not run_paper / registry in isolation).

These tests invoke ``phantom_quant.cli.main`` exactly as a user would on the
command line, plus one subprocess invocation of ``python -m phantom_quant.cli``
to prove the entry point is wired all the way through.
"""
import subprocess
import sys
from pathlib import Path

from phantom_quant.cli import main
from phantom_quant.registry import default_registry
from phantom_quant.strategy import Strategy

FIX = Path(__file__).parent / "fixtures" / "sample_2330_1d.csv"


def test_paper_subcommand_writes_report_via_real_cli(tmp_path, capsys):
    out = tmp_path / "paper.md"
    rc = main(["paper", "--csv", str(FIX), "--strategy", "sma_cross",
               "--symbol", "2330", "--cash", "1000000",
               "--short", "3", "--long", "6", "--out", str(out)])
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    # same report shape as backtest
    assert "2330" in text
    assert "trades: 2 (closed: 1)" in text  # one buy + one sell round-trip
    assert "report written" in capsys.readouterr().out


def test_paper_matches_backtest_through_the_cli(tmp_path):
    # paper trading delegates to the same primitives as backtest, so the report
    # produced through the CLI is byte-identical.
    bt = tmp_path / "bt.md"
    pp = tmp_path / "pp.md"
    common = ["--csv", str(FIX), "--strategy", "sma_cross", "--symbol", "2330",
              "--cash", "1000000", "--short", "3", "--long", "6"]
    assert main(["backtest", *common, "--out", str(bt)]) == 0
    assert main(["paper", *common, "--out", str(pp)]) == 0
    assert pp.read_text(encoding="utf-8") == bt.read_text(encoding="utf-8")


class _AlwaysFlat(Strategy):
    """Trivial strategy registered ONLY in the registry, never in cli._STRATEGIES."""

    def __init__(self, **_kwargs):  # CLI always passes short/long/qty
        pass

    def on_bar(self, bar, ctx):
        return []


def test_registry_only_strategy_is_resolvable_from_cli(tmp_path):
    # Register a strategy that exists ONLY in the registry (not in the hardcoded
    # cli._STRATEGIES dict). If the CLI can resolve it, the registry is the real
    # selection path -- not dead code.
    name = "e2e_registry_only"
    if name not in default_registry.list():
        default_registry.register(name, _AlwaysFlat)
    try:
        from phantom_quant import cli
        assert name not in cli._STRATEGIES  # prove it is NOT in the hardcoded dict
        out = tmp_path / "r.md"
        rc = main(["paper", "--csv", str(FIX), "--strategy", name,
                   "--symbol", "2330", "--cash", "1000000", "--out", str(out)])
        assert rc == 0
        assert out.exists()
    finally:
        default_registry._factories.pop(name, None)


def test_paper_runs_via_module_entrypoint(tmp_path):
    # Prove the real `python -m phantom_quant.cli paper ...` entry point works.
    out = tmp_path / "sub.md"
    proc = subprocess.run(
        [sys.executable, "-m", "phantom_quant.cli", "paper",
         "--csv", str(FIX), "--strategy", "sma_cross", "--symbol", "2330",
         "--cash", "1000000", "--short", "3", "--long", "6", "--out", str(out)],
        capture_output=True, text=True, cwd=str(Path(__file__).parent.parent),
    )
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
    assert "report written" in proc.stdout
