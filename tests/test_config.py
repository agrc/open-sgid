from cloudb import config


def test_source_connection_uses_driver_18_with_encryption(mocker):
    mocker.patch.object(
        config,
        "SRC_CONNECTION",
        {"host": "sql.example.com", "database": "sgid", "user": "test-user", "password": "test-password"},
    )

    connection = config.get_source_connection()

    assert connection.startswith("MSSQL:driver=ODBC Driver 18 for SQL Server;")
    assert "server=sql.example.com;" in connection
