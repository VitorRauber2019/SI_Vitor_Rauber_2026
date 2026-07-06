import streamlit as st
import pandas as pd
from services.formpag_service import FormaPagamentoService

st.set_page_config(page_title="Formas de Pagamento", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "forma_pag_para_editar" not in st.session_state:
    st.session_state.forma_pag_para_editar = None # Controla se estamos editando um registro

st.title("💳 Formas de Pagamento")

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.forma_pag_para_editar is not None
titulo_formulario = "✏️ Editar Forma de Pagamento" if modo_edicao else "✨ Nova Forma de Pagamento"

with st.expander(titulo_formulario, expanded=True):
    # Definição dos valores padrão (Vazio para cadastro ou preenchido para edição)
    nome_padrao = st.session_state.forma_pag_para_editar["forma_pagamento"] if modo_edicao else ""
    desc_padrao = st.session_state.forma_pag_para_editar["descricao"] if modo_edicao else ""

    col_nome, col_desc = st.columns([0.4, 0.6])
    nome_forma = col_nome.text_input("Forma de Pagamento (Ex: Cartão de Crédito, Pix)", value=nome_padrao)
    descricao_forma = col_desc.text_input("Descrição Curta (Ex: À vista ou parcelado)", value=desc_padrao)
    
    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.15, 0.15, 0.7])
    
    if modo_edicao:
        # --- AÇÕES DO MODO DE EDIÇÃO ---
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome_forma and descricao_forma:
                FormaPagamentoService.editar(
                    id_forma=st.session_state.forma_pag_para_editar["id"],
                    nome=nome_forma,
                    descricao=descricao_forma
                )
                st.success("Forma de pagamento atualizada com sucesso!")
                st.session_state.forma_pag_para_editar = None
                st.rerun()
            else:
                st.error("Todos os campos são obrigatórios.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.forma_pag_para_editar = None
            st.rerun()
    else:
        # --- AÇÕES DO MODO DE CADASTRO ---
        if col_btn_salvar.button("Salvar Forma", type="primary", use_container_width=True):
            if nome_forma and descricao_forma:
                FormaPagamentoService.criar(nome_forma, descricao_forma)
                st.success(f"Forma de pagamento '{nome_forma}' cadastrada com sucesso!")
                st.rerun()
            else:
                st.error("Todos os campos são obrigatórios.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativadas = st.checkbox("👁️ Exibir formas de pagamento desativadas (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
formas = FormaPagamentoService.listar_todas(apenas_ativos=not exibir_desativadas)

if formas:
    st.subheader("📊 Formas Cadastradas")
    
    # Tratamento estruturado dos dados para o DataFrame do Grid
    dados_grid = []
    for f in formas:
        dados_grid.append({
            "id": f['id'],
            "Forma de Pagamento": f['forma_pagamento'],
            "Descrição": f['descricao'],
            "Status": "🟢 Ativo" if f.get('ativo', True) else "🔴 Desativado"
        })
        
    df_formas = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_formas,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"), # Exibe o ID numérico perfeitamente
            "Forma de Pagamento": st.column_config.TextColumn("Forma de Pagamento", width="medium"),
            "Descrição": st.column_config.TextColumn("Descrição", width="large"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    # Se uma linha do Grid for selecionada, ativa o painel de controle inferior
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        forma_escolhida = df_formas.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{forma_escolhida['id']}** - **{forma_escolhida['Forma de Pagamento']}**")
        
        # 1. BOTÃO EDITAR SELECIONADO
        if c_edit.button("✏️ Editar Selecionada", use_container_width=True):
            st.session_state.forma_pag_para_editar = {
                "id": int(forma_escolhida['id']),
                "forma_pagamento": forma_escolhida['Forma de Pagamento'],
                "descricao": forma_escolhida['Descrição']
            }
            st.rerun()
            
        # 2. BOTÃO SOFT DELETE (ALTERNAR STATUS LOGICO)
        esta_ativa = "🟢 Ativo" in forma_escolhida['Status']
        texto_botao = "❌ Desativar" if esta_ativa else "🔄 Reativar"
        cor_botao = "primary" if esta_ativa else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            FormaPagamentoService.alternar_status(int(forma_escolhida['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhuma forma de pagamento localizada com os filtros aplicados.")