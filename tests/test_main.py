from unittest.mock import call

import pytest

from cloudb import main


def test_sync_runs_operations_in_order(mocker):
    calls = []
    trim = mocker.patch.object(main, "trim", side_effect=lambda dry_run: calls.append(("trim", dry_run)))
    import_data = mocker.patch.object(
        main, "import_data", side_effect=lambda skip_if_exists, missing, dry_run: calls.append(("import", dry_run))
    )
    get_tables = mocker.patch.object(
        main, "get_tables_from_change_detection", side_effect=lambda: calls.append(("change detection",)) or ["water.rivers"]
    )
    update = mocker.patch.object(main, "update", side_effect=lambda tables, dry_run: calls.append(("update", dry_run)))

    main.sync(dry_run=True)

    assert trim.call_args == call(True)
    assert import_data.call_args == call(False, True, True)
    assert get_tables.call_count == 1
    assert update.call_args == call(["water.rivers"], True)
    assert calls == [("trim", True), ("import", True), ("change detection",), ("update", True)]


def test_sync_raises_after_running_all_stages(mocker):
    trim = mocker.patch.object(main, "trim", side_effect=RuntimeError("trim failed"))
    import_data = mocker.patch.object(main, "import_data")
    get_tables = mocker.patch.object(main, "get_tables_from_change_detection", return_value=[])
    update = mocker.patch.object(main, "update")

    with pytest.raises(RuntimeError, match="trim failed"):
        main.sync()

    assert trim.call_count == 1
    assert import_data.call_count == 1
    assert get_tables.call_count == 1
    assert update.call_count == 1


def test_check_if_exists_returns_true_for_cached_table(mocker):
    main.CONNECTION_TABLE_CACHE.clear()
    main.CONNECTION_TABLE_CACHE["connection"] = ["water.rivers"]

    populate_cache = mocker.patch.object(main, "_populate_table_cache")

    assert main._check_if_exists("connection", "water", "rivers", {}) is True
    populate_cache.assert_not_called()


def test_check_if_exists_populates_cache_on_miss(mocker):
    main.CONNECTION_TABLE_CACHE.clear()

    def populate_cache(connection_string):
        main.CONNECTION_TABLE_CACHE[connection_string] = ["water.rivers"]

    populate_cache_mock = mocker.patch.object(main, "_populate_table_cache", side_effect=populate_cache)

    assert main._check_if_exists("connection", "water", "rivers", {}) is True
    populate_cache_mock.assert_called_once_with("connection")
