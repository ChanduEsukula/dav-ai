"""Shared pytest configuration.

Backend tests should not read from or write to the real DATABASE_URL by default.
Individual tests that need to validate database configuration should monkeypatch
DATABASE_URL explicitly inside that test.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolate_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent tests from using the developer's real configured database."""

    monkeypatch.delenv("DATABASE_URL", raising=False)

def pytest_addoption(parser):
    parser.addoption("--require-pharma-artifact", action="store_true",
                     help="Required release-integration gate: missing/corrupt artifact or skipped release checks fail")


def pytest_configure(config):
    config.addinivalue_line("markers", "release_artifact: integration check requiring the sealed external pharmaceutical release")


def pytest_sessionstart(session):
    if session.config.getoption("--require-pharma-artifact"):
        from app.db.pharma.release_connection import release_database_path, verify_artifact
        try:
            verify_artifact(release_database_path())
        except Exception as exc:
            raise pytest.UsageError(
                "RELEASE INTEGRATION BLOCKED: required pharmaceutical artifact is missing, corrupt, "
                "incompatible or inaccessible. Install the verified external release; publication approval "
                f"is unchanged. Verification error: {type(exc).__name__}"
            ) from None


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    nodes = {item.nodeid for item in items if item.get_closest_marker("release_artifact")}
    config._release_integration_nodes = nodes
    if config.getoption("--require-pharma-artifact") and not nodes:
        raise pytest.UsageError("RELEASE INTEGRATION BLOCKED: no release integration tests selected")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    if not session.config.getoption("--require-pharma-artifact"):
        return
    reporter = session.config.pluginmanager.getplugin("terminalreporter")
    passed = {r.nodeid for r in reporter.stats.get("passed", []) if r.when == "call"} if reporter else set()
    required = getattr(session.config, "_release_integration_nodes", set())
    skipped = {r.nodeid for r in reporter.stats.get("skipped", [])} if reporter else set()
    if not required or required - passed or required & skipped:
        session.exitstatus = 1
        if reporter:
            reporter.write_line("RELEASE INTEGRATION BLOCKED: every selected release check must pass; skips are not approval", red=True)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    nodes = getattr(config, "_release_integration_nodes", set())
    passed = {r.nodeid for r in terminalreporter.stats.get("passed", []) if r.when == "call"} & nodes
    terminalreporter.write_sep("-", "Pharmaceutical release integration")
    if config.getoption("--require-pharma-artifact") and nodes and passed == nodes:
        terminalreporter.write_line(f"Required gate: {len(passed)}/{len(nodes)} release checks passed; publication approval unchanged")
    elif nodes:
        terminalreporter.write_line(f"Optional run only: {len(passed)}/{len(nodes)} release checks passed. NOT a required integration gate.")
    else:
        terminalreporter.write_line("Release checks not selected. Artifact-independent results do not verify release integration.")
