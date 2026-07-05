import streamlit as st
import pandas as pd
from services.pais_service import PaisService

st.set_page_config(page_title="Gestão de Países", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "pais_para_editar" not in st.session_state:
    st.session_state.pais_para_editar = None 

st.title("🌍 Cadastro de Países")

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.pais_para_editar is not None
titulo_formulario = "✏️ Editar País" if modo_edicao else "✨ Novo País"

with st.expander(titulo_formulario, expanded=True):
    nome_padrao = st.session_state.pais_para_editar["nome"] if modo_edicao else ""
    nacionalidade_padrao = st.session_state.pais_para_editar["nacionalidade"] if modo_edicao else ""
    sigla_padrao = st.session_state.pais_para_editar["sigla"] if modo_edicao else ""

    col1, col2 = st.columns(2)
    nome = col1.text_input("País", value=nome_padrao)
    sigla = col2.text_input("Sigla (Ex: BR)", value=sigla_padrao, max_chars=3)
    nacionalidade = st.text_input("Nacionalidade", value=nacionalidade_padrao)
    
    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.15, 0.15, 0.7])
    
    if modo_edicao:
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome:
                PaisService.editar(
                    id_pais=st.session_state.pais_para_editar["id"],
                    nome=nome,
                    sigla=sigla,
                    nacionalidade=nacionalidade
                )
                st.success(f"País {nome} atualizado com sucesso!")
                st.session_state.pais_para_editar = None
                st.rerun()
            else:
                st.error("O nome do país é obrigatório.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.pais_para_editar = None
            st.rerun()
    else:
        if col_btn_salvar.button("Salvar País", type="primary", use_container_width=True):
            if nome:
                PaisService.criar(nome, sigla, nacionalidade)
                st.success(f"País {nome} cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("O nome do país é obrigatório.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativados = st.checkbox("👁️ Exibir países desativados (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
paises = PaisService.listar_todos(apenas_ativos=not exibir_desativados)

if paises:
    st.subheader("📊 Países Cadastrados")
    
    dados_grid = []
    for p in paises:
        dados_grid.append({
            "id": p['id'],
            "País": p['nome'],
            "Sigla": p.get('sigla', 'N/A'),
            "Nacionalidade": p.get('nacionalidade', 'N/A'),
            "Status": "🟢 Ativo" if p.get('ativo', True) else "🔴 Desativado"
        })
        
    df_paises = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_paises,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"), # <-- MODIFICADO: Agora exibe o ID formatado
            "País": st.column_config.TextColumn("País", width="large"),
            "Sigla": st.column_config.TextColumn("Sigla", width="small"),
            "Nacionalidade": st.column_config.TextColumn("Nacionalidade", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        pais_escolhido = df_paises.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{pais_escolhido['id']}** - **{pais_escolhido['País']}**")
        
        if c_edit.button("✏️ Editar Selecionado", use_container_width=True):
            st.session_state.pais_para_editar = {
                "id": int(pais_escolhido['id']),
                "nome": pais_escolhido['País'],
                "nacionalidade": pais_escolhido['Nacionalidade'],
                "sigla": pais_escolhido['Sigla']
            }
            st.rerun()
            
        esta_ativo = "🟢 Ativo" in pais_escolhido['Status']
        texto_botao = "❌ Desativar" if esta_ativo else "🔄 Reativar"
        cor_botao = "primary" if esta_ativo else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            PaisService.alternar_status(int(pais_escolhido['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhum país localizado com os filtros aplicados.")