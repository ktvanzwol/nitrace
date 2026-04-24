import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--system",
        action="store_true",
        default=False,
        help="Run system tests that require NI IO Trace to be installed.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--system"):
        return
    skip_system = pytest.mark.skip(reason="Need --system option to run")
    for item in items:
        if "system" in item.keywords:
            item.add_marker(skip_system)
