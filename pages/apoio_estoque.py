import streamlit as st
from services.categoria_service import CategoriaService
from services.marca_service import MarcaService

st.set_page_config(page_title="Apoio ao Estoque", layout="wide")
st.title("⚙️ Configurações de Estoque")

tab_cat, tab_marca = st.tabs(["Categorias", "Marcas"])

# --- ABA CATEGORIAS ---
with tab_cat:
    st.subheader("Gerenciar Categorias")
    with st.form("nova_categoria"):
        nome_cat = st.text_input("Nome da Categoria (Ex: Shampoos, Tinturas)")
        if st.form_submit_button("Adicionar Categoria"):
            if nome_cat:
                CategoriaService.criar(nome_cat)
                st.success(f"Categoria '{nome_cat}' adicionada!")
                st.rerun()
    
    categorias = CategoriaService.listar_todas()
    if categorias:
        for c in categorias:
            col1, col2 = st.columns([0.8, 0.2])
            col1.write(f"ID: {c['id']} | **{c['categoria']}**")
            if col2.button("Excluir", key=f"cat_{c['id']}"):
                CategoriaService.deletar(c['id'])
                st.rerun()

# --- ABA MARCAS ---
with tab_marca:
    st.subheader("Gerenciar Marcas")
    with st.form("nova_marca"):
        nome_marca = st.text_input("Nome da Marca (Ex: L'Oréal, Wella)")
        if st.form_submit_button("Adicionar Marca"):
            if nome_marca:
                MarcaService.criar(nome_marca)
                st.success(f"Marca '{nome_marca}' adicionada!")
                st.rerun()
    
    marcas = MarcaService.listar_todas()
    if marcas:
        for m in marcas:
            col1, col2 = st.columns([0.8, 0.2])
            col1.write(f"ID: {m['id']} | **{m['marca']}**")
            if col2.button("Excluir", key=f"marca_{m['id']}"):
                MarcaService.deletar(m['id'])
                st.rerun()