import streamlit as st
from services.pais_service import PaisService

st.set_page_config(page_title="Gestão de Países", layout="wide")

st.title("🌍 Cadastro de Países")

# --- FORMULÁRIO DE CADASTRO ---
with st.expander("Novo País"):
    with st.form("form_pais"):
        col1, col2 = st.columns(2)
        nome = col1.text_input("País")
        nacionalidade = col2.text_input("Nacionalidade")
        codigo = col1.text_input("Código (Ex: 1058)")
        sigla = col2.text_input("Sigla (Ex: BR)")
        
        submit = st.form_submit_button("Salvar País")
        
        if submit:
            if nome:
                PaisService.criar(nome, codigo, sigla, nacionalidade)
                st.success(f"País {nome} cadastrado!")
                st.rerun()
            else:
                st.error("O nome é obrigatório.")

# --- LISTAGEM ---
paises = PaisService.listar_todos()
if paises:
    st.subheader("Países Cadastrados")
    for p in paises:
        col_dados, col_btn = st.columns([0.8, 0.2])
        col_dados.write(f"**{p['nome']}** ({p['sigla']}) - {p['nacionalidade']}")
        
        if col_btn.button("Excluir", key=f"del_{p['id']}"):
            PaisService.deletar(p['id'])
            st.rerun()
else:
    st.info("Nenhum país cadastrado.")