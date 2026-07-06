import streamlit as st
import pandas as pd
from services.servico_service import ServicoService

st.set_page_config(page_title="Gestão de Serviços", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "servico_para_editar" not in st.session_state:
    st.session_state.servico_para_editar = None # Controla se estamos editando um serviço

st.title("✂️ Catálogo de Serviços")

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.servico_para_editar is not None
titulo_formulario = "✏️ Editar Serviço" if modo_edicao else "✨ Cadastrar Novo Serviço"

with st.expander(titulo_formulario, expanded=True):
    # Definição dos valores padrão (Vazio para cadastro ou preenchido para edição)
    nome_padrao = st.session_state.servico_para_editar["nome"] if modo_edicao else ""
    preco_padrao = float(st.session_state.servico_para_editar["preco"]) if modo_edicao else 0.0
    duracao_padrao = int(st.session_state.servico_para_editar["duracao_minutos"]) if modo_edicao else 30

    nome = st.text_input("Nome do Serviço (Ex: Corte Masculino, Coloração)", value=nome_padrao)
    
    col1, col2 = st.columns(2)
    preco = col1.number_input("Preço de Venda (R$)", min_value=0.0, step=5.0, value=preco_padrao)
    duracao = col2.number_input("Duração Estimada (Minutos)", min_value=1, step=15, value=duracao_padrao)
    
    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.15, 0.15, 0.7])
    
    if modo_edicao:
        # --- AÇÕES DO MODO DE EDIÇÃO ---
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome:
                ServicoService.editar(
                    id_servico=st.session_state.servico_para_editar["id"],
                    nome=nome,
                    preco=preco,
                    duracao=duracao
                )
                st.success("Serviço atualizado com sucesso!")
                st.session_state.servico_para_editar = None
                st.rerun()
            else:
                st.error("O nome do serviço é obrigatório.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.servico_para_editar = None
            st.rerun()
    else:
        # --- AÇÕES DO MODO DE CADASTRO ---
        if col_btn_salvar.button("Salvar Serviço", type="primary", use_container_width=True):
            if nome:
                ServicoService.criar(nome, preco, duracao)
                st.success(f"Serviço '{nome}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("O nome do serviço é obrigatório.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativados = st.checkbox("👁️ Exibir serviços desativados (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
servicos = ServicoService.listar_todos(apenas_ativos=not exibir_desativados)

if servicos:
    st.subheader("📊 Serviços Cadastrados")
    
    # Tratamento estruturado dos dados para o DataFrame do Grid
    dados_grid = []
    for s in servicos:
        # Formata o tempo para exibição amigável na tabela (Ex: 90 -> 1h 30min)
        horas = s['duracao_minutos'] // 60
        mins = s['duracao_minutos'] % 60
        tempo_str = f"{horas}h {mins}min" if horas > 0 else f"{mins}min"
        
        dados_grid.append({
            "id": s['id'],
            "Serviço": s['nome'],
            "Preço": f"R$ {s['preco']:.2f}",
            "Duração": f"⏳ {tempo_str}",
            "Status": "🟢 Ativo" if s.get('ativo', True) else "🔴 Desativado",
            # Guardamos os valores originais brutos ocultos para a reconstrução da edição
            "raw_preco": s['preco'],
            "raw_duracao": s['duracao_minutos']
        })
        
    df_servicos = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_servicos,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "raw_preco": None, 
            "raw_duracao": None, # Oculta os dados brutos da tabela
            "Serviço": st.column_config.TextColumn("Serviço", width="large"),
            "Preço": st.column_config.TextColumn("Preço", width="small"),
            "Duração": st.column_config.TextColumn("Duração", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    # Se uma linha do Grid for selecionada, ativa o painel de gerenciamento inferior
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        servico_escolhido = df_servicos.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{servico_escolhido['id']}** - **{servico_escolhido['Serviço']}**")
        
        # 1. BOTÃO EDITAR SELECIONADO
        if c_edit.button("✏️ Editar Selecionado", use_container_width=True):
            st.session_state.servico_para_editar = {
                "id": int(servico_escolhido['id']),
                "nome": servico_escolhido['Serviço'],
                "preco": float(servico_escolhido['raw_preco']),
                "duracao_minutos": int(servico_escolhido['raw_duracao'])
            }
            st.rerun()
            
        # 2. BOTÃO SOFT DELETE (ALTERNAR STATUS LÓGICO)
        esta_ativo = "🟢 Ativo" in servico_escolhido['Status']
        texto_botao = "❌ Desativar" if esta_ativo else "🔄 Reativar"
        cor_botao = "primary" if esta_ativo else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            ServicoService.alternar_status(int(servico_escolhido['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhum serviço localizado com os filtros aplicados.")