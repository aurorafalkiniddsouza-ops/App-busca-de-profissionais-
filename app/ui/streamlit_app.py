import pandas as pd
import streamlit as st


st.set_page_config(page_title="Busca de profissionais", layout="wide")

st.title("Busca de profissionais por conselho")
st.caption("MVP inicial para validar profissionais em bases públicas de conselhos de classe.")

uploaded_file = st.file_uploader("Envie a planilha Excel", type=["xlsx"])
selected_council = st.selectbox("Conselho", ["COREN-SP", "CREMESP"])
state_filter = st.text_input("UF (opcional)", value="SP")

if uploaded_file:
    dataframe = pd.read_excel(uploaded_file)
    st.subheader("Pré-visualização")
    st.dataframe(dataframe, use_container_width=True)

    if "nome" not in dataframe.columns:
        st.error("A planilha deve conter uma coluna chamada 'nome'.")
    else:
        st.success(f"Planilha válida. Conselho selecionado: {selected_council}.")
        st.info("Próxima etapa: conectar esta interface ao serviço de busca e à exportação de resultados.")
