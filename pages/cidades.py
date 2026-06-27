import streamlit as st
from services.cidade_service import CidadeService
from services.estado_service import EstadoService

st.set_page_config(page_title="Gestão de Cidades", layout="wide")

st.title("🏙️ Cadastro de Cidades")

estados = EstadoService.listar_todos()
estados_dict = {f"{e['nome']} ({e['uf']})": e['id'] for e in estados}

with st.expander("Nova Cidade"):
    if not estados:
        st.warning("Cadastre um estado antes de adicionar uma cidade.")
    else:
        with st.form("form_cidade"):
            col1, col2, col3 = st.columns([0.5, 0.2, 0.3])
            nome = col1.text_input("Cidade")
            ibge = col2.text_input("Código IBGE")
            estado_label = col3.selectbox("Estado", options=list(estados_dict.keys()))
            
            submit = st.form_submit_button("Salvar Cidade")
            
            if submit:
                if nome:
                    CidadeService.criar(nome, ibge, estados_dict[estado_label])
                    st.success(f"Cidade {nome} guardada!")
                    st.rerun()
                else:
                    st.error("O nome da cidade é obrigatório.")

cidades = CidadeService.listar_todos()
if cidades:
    st.subheader("Cidades Registadas")
    for cid in cidades:
        col_dados, col_btn = st.columns([0.8, 0.2])
        est_info = cid.get('estado', {})
        label_estado = f"{est_info.get('nome')} - {est_info.get('uf')}"
        col_dados.write(f"**{cid['nome']}** (IBGE: {cid['codigo_ibge'] or 'N/A'}) - {label_estado}")
        
        if col_btn.button("Excluir", key=f"del_cid_{cid['id']}"):
            CidadeService.deletar(cid['id'])
            st.rerun()