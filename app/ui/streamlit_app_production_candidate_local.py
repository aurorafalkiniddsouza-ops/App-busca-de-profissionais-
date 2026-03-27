import asyncio
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.exporter import dataframe_to_excel_bytes
from app.services.search_service_production_candidate import process_dataframe


st.set_page_config(page_title="Busca de profissionais", layout="wide")

st.title("Busca de profissionais por conselho")
st.caption("Versão candidata de produção com conector validado do CREMESP.")

uploaded_file = st.file_uploader("Envie a planilha Excel", type=["xlsx"])
selected_council = st.selectbox("Conselho", ["CREMESP", "COREN-SP"])
state_filter = st.text_input("UF (opcional)", value="SP")

if uploaded_file:
    input_dataframe = pd.read_excel(uploaded_file)
    st.subheader("Pré-visualização da entrada")
    st.dataframe(input_dataframe, use_container_width=True)

    if "nome" not in input_dataframe.columns:
        st.error("A planilha deve conter uma coluna chamada 'nome'.")
    elif st.button("Processar consultas"):
        with st.spinner("Processando consultas..."):
            result_dataframe = asyncio.run(
                process_dataframe(
                    dataframe=input_dataframe,
                    council=selected_council,
                    searched_state=state_filter or None,
                )
            )

        st.subheader("Resultado")
        st.dataframe(result_dataframe, use_container_width=True)

        if not result_dataframe.empty:
            totals = result_dataframe["final_status"].value_counts(dropna=False).reset_index()
            totals.columns = ["status", "quantidade"]
            st.subheader("Resumo executivo")
            st.dataframe(totals, use_container_width=True)

        excel_bytes = dataframe_to_excel_bytes(result_dataframe)
        st.download_button(
            label="Baixar resultado em Excel",
            data=excel_bytes,
            file_name="resultado_busca_profissionais.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
