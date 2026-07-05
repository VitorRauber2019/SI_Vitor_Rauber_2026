import streamlit as st
import pandas as pd
from services.estado_service import EstadoService
from services.pais_service import PaisService

st.set_page_config(page_title="Gestão de Estados", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "estado_para_editar" not in st.session_state:
    st.session_state.estado_para_editar = None # Controla se estamos editando um estado

if "pais_selecionado" not in st.session_state:
    st.session_state.pais_selecionado = None # Vinculo de país para novo Estado

if "pais_selecionado_edicao" not in st.session_state:
    st.session_state.pais_selecionado_edicao = None # Vinculo de país para edição de Estado

if "pais_para_editar" not in st.session_state:
    st.session_state.pais_para_editar = None # Controla se estamos modificando um País inline

st.title("🏛️ Cadastro de Estados")

# --- CONTEÚDO DE GERENCIAMENTO DE PAÍSES (Renderizado dentro do Popover) ---
def renderizar_gerenciador_paises(prefix="estado_page"):
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar País", "➕ Novo País"])
    
    with tab_sel:
        exibir_p_desativados = st.checkbox("👁️ Exibir países desativados", value=False, key=f"{prefix}_chk_p_desat")
        paises = PaisService.listar_todos(apenas_ativos=not exibir_p_desativados)
        
        if not paises:
            st.info("Nenhum país cadastrado.")
        else:
            dados_p = []
            for p in paises:
                dados_p.append({
                    "id": p["id"],
                    "País": p["nome"],
                    "Sigla": p["sigla"],
                    "Nacionalidade": p["nacionalidade"],
                    "Status": "🟢 Ativo" if p.get("ativo", True) else "🔴 Desativado"
                })
            df_paises = pd.DataFrame(dados_p)
            event = st.dataframe(
                df_paises,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"), # <-- MODIFICADO: Exibe o ID do País no Pop-up
                    "País": "País", 
                    "Sigla": "Sigla", 
                    "Nacionalidade": "Nacionalidade", 
                    "Status": "Status"
                },
                use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row",
                key=f"{prefix}_grid_paises"
            )
            
            if event.selection.rows:
                idx = event.selection.rows[0]
                escolhido = df_paises.iloc[idx]
                
                st.write("")
                c_sel, c_edit, c_del = st.columns(3)
                
                # 1. Botão para selecionar e vincular o país ao estado atual
                if escolhido["Status"] == "🟢 Ativo":
                    if c_sel.button("🎯 Selecionar", use_container_width=True, key=f"{prefix}_btn_sel_p"):
                        if st.session_state.estado_para_editar is not None:
                            st.session_state.pais_selecionado_edicao = {"label": escolhido['País'], "id": int(escolhido['id'])}
                        else:
                            st.session_state.pais_selecionado = {"label": escolhido['País'], "id": int(escolhido['id'])}
                        st.rerun()
                else:
                    c_sel.button("🎯 Bloqueado", disabled=True, use_container_width=True, key=f"{prefix}_btn_sel_p_dis")
                
                # 2. Ativar formulário de Edição inline de País
                if c_edit.button("✏️ Editar", use_container_width=True, key=f"{prefix}_btn_edit_p"):
                    st.session_state.pais_para_editar = {
                        "id": int(escolhido["id"]),
                        "nome": escolhido["País"],
                        "sigla": escolhido["Sigla"],
                        "nacionalidade": escolhido["Nacionalidade"]
                    }
                    st.rerun()
                
                # 3. Soft Delete / Reativação de País
                esta_ativa_p = escolhido["Status"] == "🟢 Ativo"
                txt_p_btn = "❌ Desativar" if esta_ativa_p else "🔄 Reativar"
                type_p_btn = "primary" if esta_ativa_p else "secondary"
                
                if c_del.button(txt_p_btn, type=type_p_btn, use_container_width=True, key=f"{prefix}_btn_del_p"):
                    PaisService.alternar_status(int(escolhido["id"]))
                    st.rerun()
            
            # Formulário dinâmico de edição de País
            if st.session_state.pais_para_editar is not None:
                st.write("---")
                st.write("##### ✏️ Modificar País")
                with st.container(border=True):
                    edit_n = st.text_input("Nome", value=st.session_state.pais_para_editar["nome"], key=f"{prefix}_ed_p_nome")
                    edit_s = st.text_input("Sigla", value=st.session_state.pais_para_editar["sigla"], max_chars=3, key=f"{prefix}_ed_p_sigla")
                    edit_nac = st.text_input("Nacionalidade", value=st.session_state.pais_para_editar["nacionalidade"], key=f"{prefix}_ed_p_nac")
                    
                    cs1, cs2 = st.columns(2)
                    if cs1.button("Salvar Alterações", type="primary", use_container_width=True, key=f"{prefix}_btn_save_p"):
                        if edit_n:
                            PaisService.editar(st.session_state.pais_para_editar["id"], edit_n, edit_s, edit_nac)
                            st.session_state.pais_para_editar = None
                            st.rerun()
                    if cs2.button("Cancelar", use_container_width=True, key=f"{prefix}_btn_canc_p"):
                        st.session_state.pais_para_editar = None
                        st.rerun()

    with tab_cad:
        with st.form(f"{prefix}_form_novo_pais", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_pais = c1.text_input("Nome do País")
            s_pais = c2.text_input("Sigla", max_chars=3)
            nacionalidade = st.text_input("Nacionalidade")
            if st.form_submit_button("Salvar País"):
                if n_pais:
                    PaisService.criar(nome=n_pais, sigla=s_pais, nacionalidade=nacionalidade)
                    st.success("País cadastrado!")
                    st.rerun()

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.estado_para_editar is not None
titulo_formulario = "✏️ Editar Estado" if modo_edicao else "✨ Novo Estado"

with st.expander(titulo_formulario, expanded=True):
    # Definição dos valores padrão para os inputs de texto
    nome_padrao = st.session_state.estado_para_editar["nome"] if modo_edicao else ""
    uf_padrao = st.session_state.estado_para_editar["uf"] if modo_edicao else ""
    
    # Determina qual estado de sessão escutar para o País selecionado
    p_atual = st.session_state.pais_selecionado_edicao if modo_edicao else st.session_state.pais_selecionado
    txt_p = p_atual['label'] if p_atual else "Selecionar País..."

    col_nome, col_uf, col_pais, col_btn_salvar, col_btn_cancelar = st.columns([0.3, 0.15, 0.25, 0.15, 0.15])
    
    nome_estado = col_nome.text_input("Estado", value=nome_padrao)
    uf_estado = col_uf.text_input("UF", value=uf_padrao, max_chars=2).upper()
    
    # Substituído selectbox pelo Popover dinâmico gerenciável
    col_pais.write("**País Pertencente**")
    with col_pais.popover(txt_p, icon="🌎", use_container_width=True):
        renderizar_gerenciador_paises(prefix="edit_estado" if modo_edicao else "cad_estado")
    
    col_btn_salvar.write("")
    col_btn_salvar.write("")
    col_btn_cancelar.write("")
    col_btn_cancelar.write("")
    
    if modo_edicao:
        # --- AÇÕES DO MODO DE EDIÇÃO ---
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome_estado and uf_estado and p_atual:
                EstadoService.editar(
                    id_estado=st.session_state.estado_para_editar["id"],
                    nome=nome_estado,
                    uf=uf_estado,
                    pais_id=p_atual["id"]
                )
                st.success("Estado updated!")
                st.session_state.estado_para_editar = None
                st.session_state.pais_selecionado_edicao = None
                st.rerun()
            else:
                st.error("Preencha o nome, a UF e selecione o País no gerenciador.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.estado_para_editar = None
            st.session_state.pais_selecionado_edicao = None
            st.rerun()
    else:
        # --- AÇÕES DO MODO DE CADASTRO ---
        if col_btn_salvar.button("Salvar Estado", type="primary", use_container_width=True):
            if nome_estado and uf_estado and p_atual:
                EstadoService.criar(nome_estado, uf_estado, p_atual["id"])
                st.success(f"Estado {nome_estado} cadastrado com sucesso!")
                st.session_state.pais_selecionado = None
                st.rerun()
            else:
                st.error("Preencha o nome, a UF e selecione o País no gerenciador.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativados = st.checkbox("👁️ Exibir estados desativados (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
estados = EstadoService.listar_todos(apenas_ativos=not exibir_desativados)

if estados:
    st.subheader("📊 Estados Cadastrados")
    
    dados_grid = []
    for est in estados:
        pais_rel = est.get('pais', {})
        dados_grid.append({
            "id": est['id'],
            "Estado": est['nome'],
            "UF": est['uf'],
            "País": pais_rel.get('nome', 'N/A') if pais_rel else 'N/A',
            "Status": "🟢 Ativo" if est.get('ativo', True) else "🔴 Desativado",
            "pais_id": est.get('pais_id')
        })
        
    df_estados = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_estados,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"), # <-- MODIFICADO: Exibe o ID do Estado no Grid principal
            "pais_id": None,
            "Estado": st.column_config.TextColumn("Estado", width="medium"),
            "UF": st.column_config.TextColumn("UF", width="small"),
            "País": st.column_config.TextColumn("País", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        estado_escolhido = df_estados.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{estado_escolhido['id']}** - **{estado_escolhido['Estado']} ({estado_escolhido['UF']})**")
        
        # 1. BOTÃO EDITAR SELECIONADO
        if c_edit.button("✏️ Editar Selecionado", use_container_width=True):
            st.session_state.estado_para_editar = {
                "id": int(estado_escolhido['id']),
                "nome": estado_escolhido['Estado'],
                "uf": estado_escolhido['UF']
            }
            # Vincula o país atual do estado para carregar preenchido na tela
            st.session_state.pais_selecionado_edicao = {
                "id": int(estado_escolhido['pais_id']),
                "label": estado_escolhido['País']
            }
            st.rerun()
            
        # 2. BOTÃO SOFT DELETE (ALTERNAR STATUS LOGICO)
        esta_ativo = "🟢 Ativo" in estado_escolhido['Status']
        texto_botao = "❌ Desativar" if esta_ativo else "🔄 Reativar"
        cor_botao = "primary" if esta_ativo else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            EstadoService.alternar_status(int(estado_escolhido['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhum estado localizado com os filtros aplicados.")

