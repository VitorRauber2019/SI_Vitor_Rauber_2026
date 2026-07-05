import streamlit as st
import pandas as pd
from services.categoria_service import CategoriaService

st.set_page_config(page_title="Gerenciar Categorias", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "categoria_para_editar" not in st.session_state:
    st.session_state.categoria_para_editar = None # Controla se estamos editando uma categoria

st.title("📁 Gerenciar Categorias")

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.categoria_para_editar is not None
titulo_formulario = "✏️ Editar Categoria" if modo_edicao else "✨ Nova Categoria"

with st.expander(titulo_formulario, expanded=True):
    # Definição dos valores padrão (Vazio para cadastro ou preenchido para edição)
    nome_padrao = st.session_state.categoria_para_editar["categoria"] if modo_edicao else ""

    col_input, _ = st.columns([0.7, 0.3])
    nome_cat = col_input.text_input("Nome da Categoria (Ex: Shampoos, Tinturas)", value=nome_padrao)
    
    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.3, 0.2, 0.7])
    
    if modo_edicao:
        # --- AÇÕES DO MODO DE EDIÇÃO ---
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome_cat:
                CategoriaService.editar(
                    id_cat=st.session_state.categoria_para_editar["id"],
                    nome=nome_cat
                )
                st.success("Categoria atualizada com sucesso!")
                st.session_state.categoria_para_editar = None
                st.rerun()
            else:
                st.error("O nome da categoria é obrigatório.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.categoria_para_editar = None
            st.rerun()
    else:
        # --- AÇÕES DO MODO DE CADASTRO ---
        if col_btn_salvar.button("Salvar Categoria", type="primary", use_container_width=True):
            if nome_cat:
                CategoriaService.criar(nome_cat)
                st.success(f"Categoria '{nome_cat}' cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("O nome da categoria é obrigatório.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativadas = st.checkbox("👁️ Exibir categorias desativadas (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
categorias = CategoriaService.listar_todas(apenas_ativos=not exibir_desativadas)

if categorias:
    st.subheader("📊 Categorias Cadastradas")
    
    # Tratamento estruturado dos dados para o DataFrame do Grid
    dados_grid = []
    for c in categorias:
        dados_grid.append({
            "id": c['id'],
            "Categoria": c['categoria'],
            "Status": "🟢 Ativo" if c.get('ativo', True) else "🔴 Desativado"
        })
        
    df_categorias = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_categorias,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"), # Exibe o ID do registro
            "Categoria": st.column_config.TextColumn("Categoria", width="large"),
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
        categoria_escolhida = df_categorias.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{categoria_escolhida['id']}** - **{categoria_escolhida['Categoria']}**")
        
        # 1. BOTÃO EDITAR SELECIONADO
        if c_edit.button("✏️ Editar Selecionada", use_container_width=True):
            st.session_state.categoria_para_editar = {
                "id": int(categoria_escolhida['id']),
                "categoria": categoria_escolhida['Categoria']
            }
            st.rerun()
            
        # 2. BOTÃO SOFT DELETE (ALTERNAR STATUS LOGICO)
        esta_ativa = "🟢 Ativo" in categoria_escolhida['Status']
        texto_botao = "❌ Desativar" if esta_ativa else "🔄 Reativar"
        cor_botao = "primary" if esta_ativa else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            CategoriaService.alternar_status(int(categoria_escolhida['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhuma categoria localizada com os filtros aplicados.")