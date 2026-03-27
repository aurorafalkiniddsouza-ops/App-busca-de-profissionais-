from io import BytesIO

import pandas as pd



def dataframe_to_excel_bytes(dataframe: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="resultado")
    buffer.seek(0)
    return buffer.getvalue()
