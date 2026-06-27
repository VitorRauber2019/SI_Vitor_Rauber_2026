import streamlit as st
from services.unidade_medida_service import UnidadeMedidaService

st.set_page_config(page_title="Unidades de Medida", layout="wide")
st.title("⚖️ Unidades de Medida")

with st.expander("Nova Unidade"):
    with st.form("form_unidade"):
        col1, col2 = st.columns([0.7, 0.3])
        nome = col1.text_input("Nome (Ex: Mililitros, Gramas)")
        sigla = col2.text_input("Sigla (Ex: ml, g)")
        
        if st.form_submit_button("Salvar"):
            if nome and sigla:
                UnidadeMedidaService.criar(nome, sigla)
                st.success(f"Unidade {sigla} criada!")
                st.rerun()

unidades = UnidadeMedidaService.listar_todas()
if unidades:
    for u in unidades:
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"**{u['unidade_medida']}** ({u['sigla']})")
        if c2.button("Excluir", key=f"un_{u['id']}"):
            UnidadeMedidaService.deletar(u['id'])
            st.rerun()