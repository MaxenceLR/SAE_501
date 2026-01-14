from unittest.mock import MagicMock
from poc_global import insert_solutions

def test_insert_solutions_success():
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    insert_solutions(5, [10, 20], conn=mock_conn)

    mock_cursor.executemany.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
