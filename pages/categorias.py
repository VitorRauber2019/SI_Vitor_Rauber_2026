import streamlit as st
from services.categoria_service import CategoriaService

st.set_page_config(page_title="Gerenciar Categorias", layout="wide")
st.title("📁 Gerenciar Categorias")

# --- FORMULÁRIO DE CADASTRO ---
with st.form("nova_categoria"):
    nome_cat = st.text_input("Nome da Categoria (Ex: Shampoos, Tinturas)")
    if st.form_submit_button("Adicionar Categoria"):
        if nome_cat:
            CategoriaService.criar(nome_cat)
            st.success(f"Categoria '{nome_cat}' adicionada!")
            st.rerun()

# --- LISTAGEM E EXCLUSÃO ---
categorias = CategoriaService.listar_todas()
if categorias:
    for c in categorias:
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"ID: {c['id']} | **{c['categoria']}**")
        if col2.button("Excluir", key=f"cat_{c['id']}"):
            CategoriaService.deletar(c['id'])
            st.rerun()