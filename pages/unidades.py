import streamlit as st
import pandas as pd
from services.unidade_medida_service import UnidadeMedidaService

st.set_page_config(page_title="Unidades de Medida", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "unidade_para_editar" not in st.session_state:
    st.session_state.unidade_para_editar = None # Controla se estamos editando uma unidade

st.title("⚖️ Unidades de Medida")

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.unidade_para_editar is not None
titulo_formulario = "✏️ Editar Unidade" if modo_edicao else "✨ Nova Unidade"

with st.expander(titulo_formulario, expanded=True):
    # Definição dos valores padrão (Vazio para cadastro ou preenchido para edição)
    nome_padrao = st.session_state.unidade_para_editar["unidade_medida"] if modo_edicao else ""
    sigla_padrao = st.session_state.unidade_para_editar["sigla"] if modo_edicao else ""

    col1, col2 = st.columns([0.7, 0.3])
    nome = col1.text_input("Nome (Ex: Mililitros, Gramas)", value=nome_padrao)
    sigla = col2.text_input("Sigla (Ex: ml, g)", value=sigla_padrao).upper()
    
    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.3, 0.2, 0.7])
    
    if modo_edicao:
        # --- AÇÕES DO MODO DE EDIÇÃO ---
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome and sigla:
                UnidadeMedidaService.editar(
                    id_un=st.session_state.unidade_para_editar["id"],
                    nome=nome,
                    sigla=sigla
                )
                st.success("Unidade de medida atualizada com sucesso!")
                st.session_state.unidade_para_editar = None
                st.rerun()
            else:
                st.error("Todos os campos são obrigatórios.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.unidade_para_editar = None
            st.rerun()
    else:
        # --- AÇÕES DO MODO DE CADASTRO ---
        if col_btn_salvar.button("Salvar Unidade", type="primary", use_container_width=True):
            if nome and sigla:
                UnidadeMedidaService.criar(nome, sigla)
                st.success(f"Unidade {sigla} cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("Todos os campos são obrigatórios.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativados = st.checkbox("👁️ Exibir unidades desativadas (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
unidades = UnidadeMedidaService.listar_todas(apenas_ativos=not exibir_desativados)

if unidades:
    st.subheader("📊 Unidades Cadastradas")
    
    # Tratamento estruturado dos dados para o DataFrame do Grid
    dados_grid = []
    for u in unidades:
        dados_grid.append({
            "id": u['id'],
            "Unidade de Medida": u['unidade_medida'],
            "Sigla": u['sigla'],
            "Status": "🟢 Ativo" if u.get('ativo', True) else "🔴 Desativado"
        })
        
    df_unidades = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_unidades,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"), # Exibe o ID do registro
            "Unidade de Medida": st.column_config.TextColumn("Unidade de Medida", width="large"),
            "Sigla": st.column_config.TextColumn("Sigla", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    # Se uma linha do Grid for selecionada, ativa as opções de gerenciamento inferiores
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        unidade_escolhida = df_unidades.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{unidade_escolhida['id']}** - **{unidade_escolhida['Unidade de Medida']} ({unidade_escolhida['Sigla']})**")
        
        # 1. BOTÃO EDITAR SELECIONADO
        if c_edit.button("✏️ Editar Selecionada", use_container_width=True):
            st.session_state.unidade_para_editar = {
                "id": int(unidade_escolhida['id']),
                "unidade_medida": unidade_escolhida['Unidade de Medida'],
                "sigla": unidade_escolhida['Sigla']
            }
            st.rerun()
            
        # 2. BOTÃO SOFT DELETE (ALTERNAR STATUS LOGICO)
        esta_ativa = "🟢 Ativo" in unidade_escolhida['Status']
        texto_botao = "❌ Desativar" if esta_ativa else "🔄 Reativar"
        cor_botao = "primary" if esta_ativa else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            UnidadeMedidaService.alternar_status(int(unidade_escolhida['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhuma unidade de medida localizada com os filtros aplicados.")