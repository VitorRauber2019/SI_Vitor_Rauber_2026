import streamlit as st
import pandas as pd
from services.marca_service import MarcaService

st.set_page_config(page_title="Gerenciar Marcas", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "marca_para_editar" not in st.session_state:
    st.session_state.marca_para_editar = None # Controla se estamos editando uma marca

st.title("🏷️ Gerenciar Marcas")

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.marca_para_editar is not None
titulo_formulario = "✏️ Editar Marca" if modo_edicao else "✨ Nova Marca"

with st.expander(titulo_formulario, expanded=True):
    # Definição dos valores padrão (Vazio para cadastro ou preenchido para edição)
    nome_padrao = st.session_state.marca_para_editar["marca"] if modo_edicao else ""

    col_input, _ = st.columns([0.7, 0.3])
    nome_marca = col_input.text_input("Nome da Marca (Ex: L'Oréal, Wella)", value=nome_padrao)
    
    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.3, 0.2, 0.7])
    
    if modo_edicao:
        # --- AÇÕES DO MODO DE EDIÇÃO ---
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome_marca:
                MarcaService.editar(
                    id_marca=st.session_state.marca_para_editar["id"],
                    nome=nome_marca
                )
                st.success("Marca atualizada com sucesso!")
                st.session_state.marca_para_editar = None
                st.rerun()
            else:
                st.error("O nome da marca é obrigatório.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.marca_para_editar = None
            st.rerun()
    else:
        # --- AÇÕES DO MODO DE CADASTRO ---
        if col_btn_salvar.button("Salvar Marca", type="primary", use_container_width=True):
            if nome_marca:
                MarcaService.criar(nome_marca)
                st.success(f"Marca '{nome_marca}' cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("O nome da marca é obrigatório.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativadas = st.checkbox("👁️ Exibir marcas desativadas (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
marcas = MarcaService.listar_todas(apenas_ativos=not exibir_desativadas)

if marcas:
    st.subheader("📊 Marcas Cadastradas")
    
    # Tratamento estruturado dos dados para o DataFrame do Grid
    dados_grid = []
    for m in marcas:
        dados_grid.append({
            "id": m['id'],
            "Marca": m['marca'],
            "Status": "🟢 Ativo" if m.get('ativo', True) else "🔴 Desativado"
        })
        
    df_marcas = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_marcas,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"), # Exibe o ID do registro
            "Marca": st.column_config.TextColumn("Marca", width="large"),
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
        marca_escolhida = df_marcas.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{marca_escolhida['id']}** - **{marca_escolhida['Marca']}**")
        
        # 1. BOTÃO EDITAR SELECIONADO
        if c_edit.button("✏️ Editar Selecionada", use_container_width=True):
            st.session_state.marca_para_editar = {
                "id": int(marca_escolhida['id']),
                "marca": marca_escolhida['Marca']
            }
            st.rerun()
            
        # 2. BOTÃO SOFT DELETE (ALTERNAR STATUS LOGICO)
        esta_ativa = "🟢 Ativo" in marca_escolhida['Status']
        texto_botao = "❌ Desativar" if esta_ativa else "🔄 Reativar"
        cor_botao = "primary" if esta_ativa else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            MarcaService.alternar_status(int(marca_escolhida['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhuma marca localizada com os filtros aplicados.")