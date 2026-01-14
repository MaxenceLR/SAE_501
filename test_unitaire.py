from poc_global import to_excel
from poc_global import get_data_for_reporting
from unittest.mock import MagicMock
from poc_global import insert_demandes
from poc_global import insert_solutions
from poc_global import insert_full_entretien
import pandas as pd
import pandas as pd


def test_insert_demandes_success():
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    insert_demandes(10, [1, 2, 3], conn=mock_conn)

    mock_cursor.executemany.assert_called_once()
    mock_conn.commit.assert_called_once()



def test_insert_full_entretien_success():
    # Faux curseur
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [99]

    # Fausse connexion
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    data = {
        "mode": 1,
        "duree": 45,
        "sexe": 1,
        "age": 38,
        "vient_pr": 1,
        "sit_fam": 2,
        "enfant": 0,
        "modele_fam": None,
        "profession": 3,
        "ress": 2,
        "origine": 1,
        "commune": "Nantes",
        "partenaire": None
    }

    new_id = insert_full_entretien(data, conn=mock_conn)

    assert new_id == 99
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()



def test_insert_solutions_success():
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    insert_solutions(5, [10, 20], conn=mock_conn)

    mock_cursor.executemany.assert_called_once()
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_to_excel_returns_bytes():
    df = pd.DataFrame({
        "a": [1, 2],
        "b": [3, 4]
    })

    excel_bytes = to_excel(df)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0


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
