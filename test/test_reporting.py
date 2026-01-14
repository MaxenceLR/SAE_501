from poc_global import get_data_for_reporting
from unittest.mock import MagicMock
import pandas as pd

def test_get_data_for_reporting():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        {
            "num": 1,
            "date_ent": "2024-01-01",
            "sexe": 1,
            "age": 30,
            "sit_fam": 2,
            "profession": 3,
            "duree": 45,
            "commune": "Nantes",
            "mode": 1,
            "vient_pr": 1
        }
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    df = get_data_for_reporting(conn=mock_conn)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "commune" in df.columns
