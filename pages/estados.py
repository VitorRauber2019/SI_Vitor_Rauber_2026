import streamlit as st
from services.estado_service import EstadoService
from services.pais_service import PaisService

st.set_page_config(page_title="Gestão de Estados", layout="wide")

st.title("🏛️ Cadastro de Estados")

# Precisamos listar os países para o utilizador selecionar no formulário
paises = PaisService.listar_todos()
paises_dict = {p['nome']: p['id'] for p in paises}

with st.expander("Novo Estado"):
    if not paises:
        st.warning("Cadastre um país antes de adicionar um estado.")
    else:
        with st.form("form_estado"):
            col1, col2, col3 = st.columns([0.5, 0.2, 0.3])
            nome = col1.text_input("Estado")
            uf = col2.text_input("UF", max_chars=2)
            pais_nome = col3.selectbox("País", options=list(paises_dict.keys()))
            
            submit = st.form_submit_button("Salvar Estado")
            
            if submit:
                if nome and uf:
                    EstadoService.criar(nome, uf, paises_dict[pais_nome])
                    st.success(f"Estado {nome} guardado com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha todos os campos obrigatórios.")

# Listagem
estados = EstadoService.listar_todos()
if estados:
    st.subheader("Estados Registados")
    for est in estados:
        col_dados, col_btn = st.columns([0.8, 0.2])
        # Acedemos ao nome do país através da relação definida no select do service
        pais_nome = est.get('pais', {}).get('nome', 'N/A')
        col_dados.write(f"**{est['nome']}** ({est['uf']}) - País: {pais_nome}")
        
        if col_btn.button("Excluir", key=f"del_est_{est['id']}"):
            EstadoService.deletar(est['id'])
            st.rerun()