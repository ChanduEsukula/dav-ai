from __future__ import annotations

import urllib.error
from pathlib import Path

import pytest

from scripts import refresh_real_world_safety_snapshots as refresh_script


def test_parse_args_defaults_to_all() -> None:
    args = refresh_script.parse_args([])

    assert args.source == "all"
    assert args.dry_run is False


@pytest.mark.parametrize("source", ["all", "fsis", "cpsc", "openfda"])
def test_parse_args_accepts_source_options(source: str) -> None:
    args = refresh_script.parse_args(["--source", source])

    assert args.source == source


def test_parse_args_accepts_dry_run() -> None:
    args = refresh_script.parse_args(["--source", "cpsc", "--dry-run"])

    assert args.source == "cpsc"
    assert args.dry_run is True


def test_parse_args_normalizes_smart_dashes() -> None:
    args = refresh_script.parse_args(["–source", "fsis", "—dry-run"])

    assert args.source == "fsis"
    assert args.dry_run is True


def test_fetch_source_records_converts_http_error() -> None:
    def failing_fetcher() -> list[dict[str, object]]:
        raise urllib.error.HTTPError(
            url="https://example.gov/api",
            code=403,
            msg="Forbidden",
            hdrs=None,
            fp=None,
        )

    with pytest.raises(refresh_script.SourceFetchError) as exc_info:
        refresh_script.fetch_source_records(
            source_name="USDA FSIS Recall API",
            endpoint="https://www.fsis.usda.gov/fsis/api/recall/v/1",
            fetcher=failing_fetcher,
        )

    error = exc_info.value
    assert error.source_name == "USDA FSIS Recall API"
    assert error.endpoint == "https://example.gov/api"
    assert error.http_status == 403
    assert "Forbidden" in error.reason


def test_print_source_fetch_error_is_clean(capsys: pytest.CaptureFixture[str]) -> None:
    error = refresh_script.SourceFetchError(
        source_name="USDA FSIS Recall API",
        endpoint="https://www.fsis.usda.gov/fsis/api/recall/v/1",
        http_status=403,
        reason="Forbidden",
    )

    refresh_script.print_source_fetch_error(error)

    captured = capsys.readouterr()
    assert "Snapshot refresh failed" in captured.err
    assert "USDA FSIS Recall API" in captured.err
    assert "HTTP status: 403" in captured.err
    assert "Forbidden" in captured.err
    assert "Traceback" not in captured.err


def test_print_dry_run_does_not_write_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = tmp_path / "snapshot_refresh_manifest.json"
    snapshot_path = tmp_path / "cpsc_daily_products_curated_records.json"

    monkeypatch.setattr(refresh_script, "ROOT", tmp_path)
    monkeypatch.setattr(refresh_script, "SNAPSHOT_REFRESH_MANIFEST_OUT", manifest_path)

    records = [{"RecallID": 1, "Title": "Example recall"}]
    entries = [
        refresh_script.manifest_entry(
            source_id="cpsc_recalls_api",
            source_name="CPSC Recalls API",
            endpoint=refresh_script.CPSC_RECALLS_ENDPOINT,
            snapshot_path=snapshot_path,
            records=records,
            refreshed_at="2026-06-24T00:00:00+00:00",
        )
    ]

    refresh_script.print_dry_run([(snapshot_path, records)], entries)

    captured = capsys.readouterr()
    assert "Dry run" in captured.out
    assert "cpsc_recalls_api" in captured.out
    assert not manifest_path.exists()
    assert not snapshot_path.exists()


def test_cpsc_dry_run_uses_registry_aligned_source_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cpsc_snapshot_path = tmp_path / "cpsc_daily_products_curated_records.json"
    manifest_path = tmp_path / "snapshot_refresh_manifest.json"

    monkeypatch.setattr(refresh_script, "ROOT", tmp_path)
    monkeypatch.setattr(refresh_script, "CPSC_DAILY_PRODUCTS_OUT", cpsc_snapshot_path)
    monkeypatch.setattr(refresh_script, "SNAPSHOT_REFRESH_MANIFEST_OUT", manifest_path)
    monkeypatch.setattr(
        refresh_script,
        "fetch_cpsc_daily_product_records",
        lambda *, max_records: [{"RecallID": 10826, "Title": "Example CPSC recall"}],
    )

    refresh_script.main(["--source", "cpsc", "--dry-run"])

    captured = capsys.readouterr()
    assert "cpsc_recalls_api" in captured.out
    assert "CPSC Recalls API" in captured.out
    assert not cpsc_snapshot_path.exists()
    assert not manifest_path.exists()
