import os
import pytest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pvs_testing')))

import pvs_testing as ms  # This should match your module name exactly


def test_no_tables_directory(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    # tmp_path has no tables subdirectory
    result = _fetch_all_sql_files(str(tmp_path))
    assert result == []
    assert any("No tables directory" in msg for msg in caplog.messages)

def test_folder_list_env_not_set(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.delenv("FOLDER_LIST", raising=False)
    ret = main()
    assert ret is None
    assert any("FOLDER_LIST environment variable not found" in msg for msg in caplog.messages)

def test_folder_list_env_invalid_json(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.setenv("FOLDER_LIST", "invalid-json")
    ret = main()
    assert ret is None
    assert any("Failed to parse FOLDER_LIST" in msg for msg in caplog.messages)


def test_fetch_all_sql_files(tmp_path):
    tables_path = tmp_path / "tables"
    tables_path.mkdir()
    sql_file = tables_path / "test_proc.sql"
    sql_file.write_text("SELECT 1")

    result = ms._fetch_all_sql_files(str(tmp_path))
    assert len(result) == 1
    assert result[0].endswith("test_proc.sql")


def test_extract_proc_names_from_file(tmp_path):
    sql_file = tmp_path / "sample.sql"
    sql_file.write_text("""
        CREATE PROCEDURE mydb.${dbEnv}.my_proc()
        REPLACE PROCEDURE mydb.${dbEnv}.another_proc()
    """)
    procs = ms._extract_proc_names_from_file(str(sql_file))
    assert "mydb.${dbEnv}.my_proc" in procs
    assert "mydb.${dbEnv}.another_proc" in procs


@patch("pvs_testing._fetch_all_sql_files")
@patch("pvs_testing._extract_proc_names_from_file")
@patch.dict(os.environ, {"TDV_ENV": "DEV"})
def test_get_final_proc_list(mock_extract, mock_fetch):
    mock_fetch.return_value = ["dummy.sql"]
    mock_extract.return_value = ["mydb.${dbEnv}.proc1", "mydb.${dbEnv}.proc1"]
    result = ms._get_final_proc_list(["folder1"])
    assert len(result) == 1
    assert result[0] == "mydb._DEV.proc1()"


@patch("pandas.read_sql")
def test_execute_tdv_query_success(mock_read_sql):
    mock_df = MagicMock()
    mock_df.to_dict.return_value = {"key": [1]}
    mock_read_sql.return_value = mock_df

    td_conn = MagicMock()
    result = ms.execute_tdv_query(td_conn, "SELECT *")
    assert result == {"key": [1]}


@patch("pandas.read_sql", side_effect=Exception("DB error"))
def test_execute_tdv_query_failure(mock_read_sql):
    td_conn = MagicMock()
    result = ms.execute_tdv_query(td_conn, "SELECT *")
    assert result == {}


def test_pass_or_fail_pass(capsys):
    result_dict = {"TEST_STATUS": ["PASSED"]}
    ms._pass_or_fail(result_dict)
    captured = capsys.readouterr()
    assert "PASSED" in captured.out or "PASSED" in captured.err


def test_pass_or_fail_fail_exit():
    result_dict = {"TEST_STATUS": ["FAILED"]}
    with pytest.raises(SystemExit):
        ms._pass_or_fail(result_dict)


@patch("pvs_testing.execute_tdv_query")
@patch("pvs_testing._pass_or_fail")
def test_run_pvs_test(mock_pass_or_fail, mock_exec):
    mock_exec.return_value = {"TEST_STATUS": ["PASSED"]}
    procs = ["proc1()", "proc2()"]
    td_conn = MagicMock()
    ms._run_pvs_test(procs, "CHG1_CTASK1", td_conn, "test_user")
    assert mock_exec.call_count == 5  # start, 2 procs, end, result
    mock_pass_or_fail.assert_called_once()


@patch.dict(os.environ, {
    "FOLDER_LIST": '["folder1"]',
    "TDV_USERNAME": "user",
    "TDV_PASSWORD": "pass",
    "ChangeTicket_Num": "123",
    "CTASK_NUM": "456"
})
@patch("pvs_testing._get_final_proc_list", return_value=["proc1()"])
@patch("pvs_testing.teradatasql.connect")
@patch("pvs_testing._run_pvs_test")
def test_main(mock_run_test, mock_connect, mock_get_procs):
    conn_context = mock_connect.return_value.__enter__.return_value
    ms.main()
    mock_get_procs.assert_called_once()
    mock_run_test.assert_called_once_with(["proc1()"], "CHG123_CTASK456", conn_context, "user")
