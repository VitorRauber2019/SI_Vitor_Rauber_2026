import streamlit as st
from services.marca_service import MarcaService

st.set_page_config(page_title="Gerenciar Marcas", layout="wide")
st.title("🏷️ Gerenciar Marcas")

# --- FORMULÁRIO DE CADASTRO ---
with st.form("nova_marca"):
    nome_marca = st.text_input("Nome da Marca (Ex: L'Oréal, Wella)")
    if st.form_submit_button("Adicionar Marca"):
        if nome_marca:
            MarcaService.criar(nome_marca)
            st.success(f"Marca '{nome_marca}' adicionada!")
            st.rerun()

# --- LISTAGEM E EXCLUSÃO ---
marcas = MarcaService.listar_todas()
if marcas:
    for m in marcas:
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"ID: {m['id']} | **{m['marca']}**")
        if col2.button("Excluir", key=f"marca_{m['id']}"):
            MarcaService.deletar(m['id'])
            st.rerun()