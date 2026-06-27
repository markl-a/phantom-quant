from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import phantom_quant


ROOT = Path(__file__).resolve().parents[1]


def _project_metadata() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as fp:
        return tomllib.load(fp)["project"]


def test_pyproject_metadata_matches_public_release_surface() -> None:
    project = _project_metadata()

    assert project["name"] == "phantom-quant"
    assert project["version"] == phantom_quant.__version__
    assert project["license"]["text"] == "Apache-2.0"
    assert project["requires-python"] == ">=3.11"
    assert project["readme"] == "README.md"
    assert project["authors"] == [{"name": "Mark Lai"}]

    deps = set(project["dependencies"])
    assert deps == {"pandas>=2", "numpy>=1.26", "pyarrow>=15"}

    classifiers = set(project["classifiers"])
    assert "Development Status :: 3 - Alpha" in classifiers
    assert "License :: OSI Approved :: Apache Software License" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Topic :: Office/Business :: Financial :: Investment" in classifiers

    urls = project["urls"]
    assert urls["Homepage"].endswith("/phantom-quant")
    assert urls["Documentation"].endswith("/phantom-quant/tree/main/docs")
    assert urls["Issues"].endswith("/phantom-quant/issues")
    assert urls["Source"].endswith("/phantom-quant")


def test_optional_dependencies_keep_live_broker_out_of_default_release() -> None:
    extras = _project_metadata()["optional-dependencies"]

    assert extras["broker"] == ["shioaji>=1"]
    assert "pytest>=7" in extras["test"]
    assert "pytest>=7" in extras["dev"]
    assert "ruff>=0.6" in extras["dev"]


def test_cli_entrypoint_target_is_importable() -> None:
    project = _project_metadata()

    assert project["scripts"]["phantom-quant"] == "phantom_quant.cli:main"
    module_name, function_name = project["scripts"]["phantom-quant"].split(":")
    module = importlib.import_module(module_name)
    assert callable(getattr(module, function_name))
