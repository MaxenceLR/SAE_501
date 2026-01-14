from poc_global import insert_full_entretien
from unittest.mock import MagicMock


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
