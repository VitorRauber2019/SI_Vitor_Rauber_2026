import streamlit as st
import pandas as pd
from services.cidade_service import CidadeService
from services.estado_service import EstadoService
from services.pais_service import PaisService 

st.set_page_config(page_title="Gestão Geográfica", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "pais_selecionado" not in st.session_state:
    st.session_state.pais_selecionado = None # Para o cadastro de Estado

if "estado_selecionado" not in st.session_state:
    st.session_state.estado_selecionado = None # Para o cadastro/edição de Cidade

if "cidade_para_editar" not in st.session_state:
    st.session_state.cidade_para_editar = None # Controla a edição de cidade

# Estados de sessão para controle interno de edição de Países e Estados
if "pais_para_editar" not in st.session_state:
    st.session_state.pais_para_editar = None

if "estado_para_editar" not in st.session_state:
    st.session_state.estado_para_editar = None

if "pais_selecionado_edicao" not in st.session_state:
    st.session_state.pais_selecionado_edicao = None # Para alterar o país ao editar um Estado

st.title("🏙️ Cadastro de Cidades")

# --- CONTEÚDO DE GERENCIAMENTO DE PAÍSES (Tratado dinamicamente com prefixo) ---
def renderizar_gerenciador_paises(prefix="padrao"):
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
                    "id": st.column_config.NumberColumn("ID", width="small"), # <-- MODIFICADO: Exibe ID do País
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
                
                # 1. Selecionar o País para vincular ao Estado
                if escolhido["Status"] == "🟢 Ativo":
                    if c_sel.button("🎯 Selecionar", use_container_width=True, key=f"{prefix}_btn_sel_p"):
                        if st.session_state.estado_para_editar is not None:
                            st.session_state.pais_selecionado_edicao = {"label": escolhido['País'], "id": int(escolhido['id'])}
                        else:
                            st.session_state.pais_selecionado = {"label": escolhido['País'], "id": int(escolhido['id'])}
                        st.rerun()
                else:
                    c_sel.button("🎯 Bloqueado", disabled=True, use_container_width=True, key=f"{prefix}_btn_sel_p_dis")
                
                # 2. Ativar formulário de Edição de País
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
            
            # Formulário inline de edição caso selecionado
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

# --- MODAL DE ESTADOS (Mantido como Dialog) ---
@st.dialog("Gerenciar Estados", width="large")
def gerenciar_estados_modal():
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Estado", "➕ Novo Estado"])
    
    with tab_sel:
        exibir_e_desativados = st.checkbox("👁️ Exibir estados desativados", value=False, key="chk_e_desat")
        estados = EstadoService.listar_todos(apenas_ativos=not exibir_e_desativados)
        
        if not estados:
            st.info("Nenhum estado cadastrado.")
        else:
            data = []
            for e in estados:
                data.append({
                    "id": e['id'],
                    "Estado": e['nome'], 
                    "UF": e['uf'], 
                    "País": e.get('pais', {}).get('nome', 'N/A'),
                    "Status": "🟢 Ativo" if e.get('ativo', True) else "🔴 Desativado",
                    "pais_id": e.get('pais_id')
                })
            df_est = pd.DataFrame(data)
            event = st.dataframe(
                df_est,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"), # <-- MODIFICADO: Exibe ID do Estado
                    "pais_id": None
                },
                use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row",
                key="grid_estados"
            )
            
            if event.selection.rows:
                idx = event.selection.rows[0]
                escolhido = df_est.iloc[idx]
                
                st.write("")
                c_sel, c_edit, c_del = st.columns(3)
                
                # 1. Selecionar o Estado para a Cidade
                if escolhido["Status"] == "🟢 Ativo":
                    if c_sel.button("🎯 Selecionar Estado", use_container_width=True, key="btn_sel_e"):
                        st.session_state.estado_selecionado = {"label": f"{escolhido['Estado']} ({escolhido['UF']})", "id": int(escolhido['id'])}
                        st.rerun()
                else:
                    c_sel.button("🎯 Bloqueado", disabled=True, use_container_width=True, key="btn_sel_e_dis")
                
                # 2. Ativar formulário de Edição de Estado
                if c_edit.button("✏️ Editar", use_container_width=True, key="btn_edit_e"):
                    st.session_state.estado_para_editar = {
                        "id": int(escolhido["id"]),
                        "nome": escolhido["Estado"],
                        "uf": escolhido["UF"]
                    }
                    st.session_state.pais_selecionado_edicao = {"label": escolhido["País"], "id": int(escolhido["pais_id"])}
                    st.rerun()
                
                # 3. Soft Delete / Reativação de Estado
                esta_ativa_e = escolhido["Status"] == "🟢 Ativo"
                txt_e_btn = "❌ Desativar" if esta_ativa_e else "🔄 Reativar"
                type_e_btn = "primary" if esta_ativa_e else "secondary"
                
                if c_del.button(txt_e_btn, type=type_e_btn, use_container_width=True, key="btn_del_e"):
                    EstadoService.alternar_status(int(escolhido["id"]))
                    st.rerun()
            
            # Formulário inline de edição de Estado caso selecionado
            if st.session_state.estado_para_editar is not None:
                st.write("---")
                st.write("##### ✏️ Modificar Estado")
                with st.container(border=True):
                    edit_nome_e = st.text_input("Nome do Estado", value=st.session_state.estado_para_editar["nome"])
                    edit_uf_e = st.text_input("UF", value=st.session_state.estado_para_editar["uf"], max_chars=2).upper()
                    
                    p_edit_atual = st.session_state.pais_selecionado_edicao
                    txt_p_edit = p_edit_atual['label'] if p_edit_atual else "Selecionar País..."
                    
                    st.write("**País Pertencente**")
                    with st.popover(txt_p_edit, icon="🌎", use_container_width=True):
                        renderizar_gerenciador_paises(prefix="edit_estado")
                        
                    ce1, ce2 = st.columns(2)
                    if ce1.button("Salvar Alterações", type="primary", use_container_width=True, key="btn_save_e"):
                        if edit_nome_e and edit_uf_e and p_edit_atual:
                            EstadoService.editar(st.session_state.estado_para_editar["id"], edit_nome_e, edit_uf_e, p_edit_atual["id"])
                            st.session_state.estado_para_editar = None
                            st.session_state.pais_selecionado_edicao = None
                            st.rerun()
                    if ce2.button("Cancelar", use_container_width=True, key="btn_canc_e"):
                        st.session_state.estado_para_editar = None
                        st.session_state.pais_selecionado_edicao = None
                        st.rerun()

    with tab_cad:
        with st.container(border=True):
            st.write("### Novo Estado")
            nome_e = st.text_input("Nome do Estado")
            uf_e = st.text_input("UF", max_chars=2).upper()
            
            p_atual = st.session_state.pais_selecionado
            txt_p = p_atual['label'] if p_atual else "Selecionar País..."
            
            st.write("**País Pertencente**")
            with st.popover(txt_p, icon="🌎", use_container_width=True):
                renderizar_gerenciador_paises(prefix="cad_estado")
            
            st.write("") 
            if st.button("Salvar Estado", type="primary"):
                if nome_e and uf_e and p_atual:
                    EstadoService.criar(nome_e, uf_e, p_atual['id'])
                    st.success("Estado cadastrado!")
                    st.session_state.pais_selecionado = None 
                    st.rerun()
                else:
                    st.error("Preencha Nome, UF e selecione o País.")

# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.cidade_para_editar is not None
titulo_formulario = "✏️ Editar Cidade" if modo_edicao else "✨ Nova Cidade"

with st.expander(titulo_formulario, expanded=True):
    nome_padrao = st.session_state.cidade_para_editar["nome"] if modo_edicao else ""
    
    col_cid, col_est, col_btn_salvar, col_btn_cancelar = st.columns([0.3, 0.3, 0.2, 0.2])
    nome_cidade = col_cid.text_input("Nome da Cidade", value=nome_padrao)
    
    e_atual = st.session_state.estado_selecionado
    txt_e = e_atual['label'] if e_atual else "Selecionar Estado..."
    
    col_est.write("**Estado**")
    if col_est.button(txt_e, icon="📍", use_container_width=True):
        gerenciar_estados_modal()
        
    col_btn_salvar.write("")
    col_btn_salvar.write("")
    col_btn_cancelar.write("")
    col_btn_cancelar.write("")
    
    if modo_edicao:
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if nome_cidade and e_atual:
                CidadeService.editar(
                    id_cidade=st.session_state.cidade_para_editar["id"],
                    nome=nome_cidade,
                    estado_id=e_atual["id"]
                )
                st.success("Cidade updated!")
                st.session_state.cidade_para_editar = None
                st.session_state.estado_selecionado = None
                st.rerun()
            else:
                st.error("Informe o nome e o estado para salvar.")
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.cidade_para_editar = None
            st.session_state.estado_selecionado = None
            st.rerun()
    else:
        if col_btn_salvar.button("Salvar Cidade", type="primary", use_container_width=True):
            if nome_cidade and e_atual:
                CidadeService.criar(nome=nome_cidade, estado_id=e_atual['id'])
                st.success(f"Cidade {nome_cidade} cadastrada com sucesso!")
                st.session_state.estado_selecionado = None
                st.rerun()
            else:
                st.error("Informe pelo menos o nome e o estado.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativadas = st.checkbox("👁️ Exibir cidades desativadas (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
cidades = CidadeService.listar_todos(apenas_ativos=not exibir_desativadas)

if cidades:
    st.subheader("📊 Cidades Cadastradas")
    
    dados_grid = []
    for cid in cidades:
        est = cid.get('estado', {})
        dados_grid.append({
            "id": cid['id'],
            "Cidade": cid['nome'],
            "Estado": est.get('nome', 'N/A') if est else 'N/A',
            "UF": est.get('uf', 'N/A') if est else 'N/A',
            "Status": "🟢 Ativo" if cid.get('ativo', True) else "🔴 Desativado",
            "estado_id": cid.get('estado_id')
        })
    
    df_cidades = pd.DataFrame(dados_grid)
    evento_grid = st.dataframe(
        df_cidades,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"), # <-- MODIFICADO: Exibe ID da Cidade no Grid principal
            "estado_id": None,
            "Cidade": st.column_config.TextColumn("Cidade", width="large"),
            "Estado": st.column_config.TextColumn("Estado", width="medium"),
            "UF": st.column_config.TextColumn("UF", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True, hide_index=True, selection_mode="single-row", on_select="rerun"
    )
    
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        cidade_escolhida = df_cidades.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{cidade_escolhida['id']}** - **{cidade_escolhida['Cidade']} ({cidade_escolhida['UF']})**") # <-- MODIFICADO: ID no aviso
        
        if c_edit.button("✏️ Editar Selecionada", use_container_width=True):
            st.session_state.cidade_para_editar = {
                "id": int(cidade_escolhida['id']),
                "nome": cidade_escolhida['Cidade']
            }
            st.session_state.estado_selecionado = {
                "id": int(cidade_escolhida['estado_id']),
                "label": f"{cidade_escolhida['Estado']} ({cidade_escolhida['UF']})"
            }
            st.rerun()
        
        esta_ativa = "🟢 Ativo" in cidade_escolhida['Status']
        texto_botao = "❌ Desativar" if esta_ativa else "🔄 Reativar"
        cor_botao = "primary" if esta_ativa else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            CidadeService.alternar_status(int(cidade_escolhida['id']))
            st.success(f"Status alterado!")
            st.rerun()
else:
    st.info("Nenhuma cidade localizada com os filtros aplicados.")