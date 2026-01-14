from poc_global import to_excel
import pandas as pd

def test_to_excel_returns_bytes():
    df = pd.DataFrame({
        "a": [1, 2],
        "b": [3, 4]
    })

    excel_bytes = to_excel(df)

    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0
