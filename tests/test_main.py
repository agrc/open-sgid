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
