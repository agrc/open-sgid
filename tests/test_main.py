from unittest.mock import call

import pytest

from cloudb import main
from cloudb.notification import NotificationError


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
    report = mocker.patch.object(main, "send_report")

    main.sync(dry_run=True)

    assert trim.call_args == call(True)
    assert import_data.call_args == call(False, True, True)
    assert get_tables.call_count == 1
    assert update.call_args == call(["water.rivers"], True)
    assert calls == [("trim", True), ("import", True), ("change detection",), ("update", True)]
    report.assert_not_called()


def test_sync_raises_after_running_all_stages(mocker):
    trim = mocker.patch.object(main, "trim", side_effect=RuntimeError("trim failed"))
    import_data = mocker.patch.object(main, "import_data")
    get_tables = mocker.patch.object(main, "get_tables_from_change_detection", return_value=[])
    update = mocker.patch.object(main, "update")
    report = mocker.patch.object(main, "send_report")

    with pytest.raises(RuntimeError, match="trim failed"):
        main.sync()

    assert trim.call_count == 1
    assert import_data.call_count == 1
    assert get_tables.call_count == 1
    assert update.call_count == 1
    report.assert_called_once()
    assert report.call_args.args[0]["status"] == "failure"


def test_sync_reports_successfully_updated_tables_when_update_partially_fails(mocker):
    mocker.patch.object(main, "trim")
    mocker.patch.object(main, "import_data")
    mocker.patch.object(main, "get_tables_from_change_detection", return_value=["history.historictrails"])
    mocker.patch.object(
        main,
        "update",
        side_effect=main.UpdateError(["history.failed_table"], ["history.historic_trails"]),
    )
    report = mocker.patch.object(main, "send_report")

    with pytest.raises(RuntimeError, match="failed to update tables: history.failed_table"):
        main.sync()

    payload = report.call_args.args[0]
    assert payload["status"] == "failure"
    assert payload["tables"] == ["history.historic_trails"]


def test_sync_reports_success_without_masking_notification_failure(mocker):
    mocker.patch.object(main, "trim")
    mocker.patch.object(main, "import_data")
    mocker.patch.object(main, "get_tables_from_change_detection", return_value=[])
    mocker.patch.object(main, "update", return_value=["history.historic_trails"])
    mocker.patch.object(main, "update_last_check_date")
    mocker.patch.object(main, "get_change_detection_bucket")
    report = mocker.patch.object(main, "send_report", side_effect=NotificationError("webhook failed"))

    main.sync()

    report.assert_called_once()
    assert report.call_args.args[0]["status"] == "success"
    assert report.call_args.args[0]["tables"] == ["history.historic_trails"]


def test_failed_sync_preserves_original_error_when_report_fails(mocker):
    mocker.patch.object(main, "trim", side_effect=RuntimeError("trim failed"))
    mocker.patch.object(main, "import_data")
    mocker.patch.object(main, "get_tables_from_change_detection", return_value=[])
    mocker.patch.object(main, "update")
    mocker.patch.object(main, "update_last_check_date")
    mocker.patch.object(main, "get_change_detection_bucket")
    mocker.patch.object(main, "send_report", side_effect=NotificationError("webhook failed"))

    with pytest.raises(RuntimeError, match="trim failed") as raised:
        main.sync()

    assert "webhook failed" not in str(raised.value)


def test_sync_does_not_fail_for_invalid_webhook_configuration(mocker):
    mocker.patch.object(main, "trim")
    mocker.patch.object(main, "import_data")
    mocker.patch.object(main, "get_tables_from_change_detection", return_value=[])
    mocker.patch.object(main, "update")
    mocker.patch.object(main, "update_last_check_date")
    mocker.patch.object(main, "get_change_detection_bucket")
    mocker.patch.object(main.config, "GOOGLE_CHAT_WEBHOOK", 123)

    main.sync()


def test_standalone_update_reports_successful_destination_tables(mocker):
    mocker.patch.object(main, "update", return_value=["history.historic_trails"])
    report = mocker.patch.object(main, "send_report")

    main._run_update(["history.historictrails"], False)

    report.assert_called_once()
    payload = report.call_args.args[0]
    assert payload["status"] == "success"
    assert payload["tables"] == ["history.historic_trails"]
    assert payload["phases"][0]["name"] == "update"


def test_standalone_update_reports_failure_without_masking_original_error(mocker):
    mocker.patch.object(
        main,
        "update",
        side_effect=main.UpdateError(["history.historictrails"], ["history.historic_trails"]),
    )
    report = mocker.patch.object(main, "send_report")

    with pytest.raises(RuntimeError, match="failed to update tables: history.historictrails"):
        main._run_update(["history.historictrails"], False)

    report.assert_called_once()
    assert report.call_args.args[0]["status"] == "failure"
    assert report.call_args.args[0]["tables"] == ["history.historic_trails"]


def test_update_reports_only_successful_destination_tables(mocker):
    mocker.patch.object(main.config, "get_source_connection", return_value="source")
    mocker.patch.object(
        main,
        "_get_tables_with_fields",
        return_value=[
            ("history", "historictrails", []),
            ("history", "no_longer_published", []),
            ("history", "failed_table", []),
        ],
    )
    mocker.patch.object(
        main,
        "_get_table_meta",
        return_value={
            "history": {
                "historictrails": {"title": "historic_trails", "geometry_type": "POLYGON"},
                "failed_table": {"title": "failed_table", "geometry_type": "POLYGON"},
            }
        },
    )
    mocker.patch.object(main, "_replace_data", side_effect=[True, True, False])

    with pytest.raises(main.UpdateError, match="failed to update tables: history.failed_table") as raised:
        main.update(["history.historictrails"], False)

    assert raised.value.updated_tables == ["history.historic_trails"]


def test_standalone_dry_run_does_not_report(mocker):
    mocker.patch.object(main, "update")
    report = mocker.patch.object(main, "send_report")

    main._run_update(["history.historictrails"], True)

    report.assert_not_called()


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


def test_replace_data_stages_before_swapping_live_table(mocker):
    mocker.patch.object(main.config, "format_ogr_connection", return_value="postgres")
    mocker.patch.object(main.config, "get_source_connection", return_value="source")
    mocker.patch.object(main.gdal, "VectorTranslateOptions", side_effect=lambda **kwargs: kwargs["options"])
    mocker.patch.object(main.gdal, "VectorTranslate", return_value=object())
    make_valid = mocker.patch.object(main, "make_valid")
    update_schema = mocker.patch.object(main.schema, "update_schema_for")
    swap = mocker.patch.object(main, "_swap_staging_table")
    create_index = mocker.patch.object(main, "create_index")

    assert main._replace_data(
        "location",
        "address_points",
        ["fulladd"],
        {"location": {"address_points": {"title": "address_points", "geometry_type": "POINT"}}},
        False,
    )

    options = main.gdal.VectorTranslateOptions.call_args.kwargs["options"]
    staging_layer = options[options.index("-nln") + 1]
    staging_qualified_layer = f"location.{staging_layer}"

    assert staging_layer.startswith("address_points_stg_")
    main.gdal.VectorTranslate.assert_called_once_with("postgres", "source", options=options)
    make_valid.assert_called_once_with(staging_qualified_layer)
    update_schema.assert_called_once_with("location.address_points", staging_qualified_layer)
    swap.assert_called_once_with("location", staging_layer, "address_points")
    create_index.assert_called_once_with("location.address_points")
