import asyncio
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.exporter import dataframe_to_excel_bytes
from app.services.search_service_production_candidate_resilient import process_dataframe_resilient


st.set_page_config(page_title="Busca de profissionais", layout="wide")

st.title("Busca de profissionais por conselho")
st.caption("Versão resiliente para lote, com retry, pacing e visibilidade do detalhe de erro.")

uploaded_file = st.file_uploader("Envie a planilha Excel", type=["xlsx"])
selected_council = st.selectbox("Conselho", ["CREMESP", "COREN-SP"])
state_filter = st.text_input("UF (opcional)", value="SP")
retry_attempts = st.number_input("Tentativas por nome", min_value=1, max_value=5, value=2, step=1)
delay_between_rows = st.number_input("Pausa entre nomes (segundos)", min_value=0.0, max_value=10.0, value=2.0, step=0.5)
delay_between_retries = st.number_input("Pausa entre tentativas (segundos)", min_value=0.0, max_value=10.0, value=3.0, step=0.5)

if uploaded_file:
    input_dataframe = pd.read_excel(uploaded_file)
    st.subheader("Pré-visualização da entrada")
    st.dataframe(input_dataframe, use_container_width=True)

    if "nome" not in input_dataframe.columns:
        st.error("A planilha deve conter uma coluna chamada 'nome'.")
    elif st.button("Processar consultas"):
        with st.spinner("Processando consultas..."):
            result_dataframe = asyncio.run(
                process_dataframe_resilient(
                    dataframe=input_dataframe,
                    council=selected_council,
                    searched_state=state_filter or None,
                    retry_attempts=int(retry_attempts),
                    delay_between_rows_seconds=float(delay_between_rows),
                    delay_between_retries_seconds=float(delay_between_retries),
                )
            )

        st.subheader("Resultado")
        preferred_columns = [
            "searched_name",
            "council",
            "final_status",
            "found_name",
            "registration_number",
            "status_text",
            "confidence_score",
            "notes",
            "queried_at",
        ]
        visible_columns = [column for column in preferred_columns if column in result_dataframe.columns]
        st.dataframe(result_dataframe[visible_columns], use_container_width=True)

        if not result_dataframe.empty:
            totals = result_dataframe["final_status"].value_counts(dropna=False).reset_index()
            totals.columns = ["status", "quantidade"]
            st.subheader("Resumo executivo")
            st.dataframe(totals, use_container_width=True)

            error_rows = result_dataframe[result_dataframe["final_status"] == "ERRO NA CONSULTA"]
            if not error_rows.empty:
                st.subheader("Detalhe dos erros")
                st.dataframe(error_rows[[column for column in ["searched_name", "notes"] if column in error_rows.columns]], use_container_width=True)

        excel_bytes = dataframe_to_excel_bytes(result_dataframe)
        st.download_button(
            label="Baixar resultado em Excel",
            data=excel_bytes,
            file_name="resultado_busca_profissionais.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
