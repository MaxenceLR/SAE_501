from poc_global import insert_demandes
from unittest.mock import MagicMock

def test_insert_demandes_success():
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    insert_demandes(10, [1, 2, 3], conn=mock_conn)

    mock_cursor.executemany.assert_called_once()
    mock_conn.commit.assert_called_once()
