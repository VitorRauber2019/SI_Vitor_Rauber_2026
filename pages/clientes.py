import streamlit as st
import pandas as pd
from services.cliente_service import ClienteService
from services.cidade_service import CidadeService
from services.estado_service import EstadoService 
from services.pais_service import PaisService
from utils.utils import validar_cpf
from datetime import date

st.set_page_config(page_title="Gestão de Clientes", layout="wide")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "cliente_para_editar" not in st.session_state:
    st.session_state.cliente_para_editar = None

# Guarda o objeto da cidade atualmente selecionada para o cliente de forma persistente
if "cidade_selecionada_cliente" not in st.session_state:
    st.session_state.cidade_selecionada_cliente = None

# Estados de controle do assistente geográfico interno
if "mostrar_dialog_cidades" not in st.session_state:
    st.session_state.mostrar_dialog_cidades = False

if "pais_selecionado_geo" not in st.session_state:
    st.session_state.pais_selecionado_geo = None

if "estado_selecionado_geo" not in st.session_state:
    st.session_state.estado_selecionado_geo = None

st.title("👤 Cadastro de Clientes")


# --- ASSISTENTE GEOGRÁFICO MULTINÍVEL (Dialog -> Popover -> Popover) ---

def renderizar_gerenciador_paises():
    """Nível 3: Popover de Países"""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar País", "➕ Novo País"])
    with tab_sel:
        p_list = PaisService.listar_todos()
        if not p_list:
            st.info("Nenhum país cadastrado.")
        else:
            df_p = pd.DataFrame(p_list)[['id', 'nome', 'sigla']]
            evt = st.dataframe(df_p, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="grid_p_geo")
            if evt.selection.rows:
                idx = evt.selection.rows[0]
                escolhido = df_p.iloc[idx]
                st.session_state.pais_selecionado_geo = {"label": escolhido['nome'], "id": int(escolhido['id'])}
                st.rerun()
    with tab_cad:
        with st.form("form_p_geo", clear_on_submit=True):
            n = st.text_input("Nome do País")
            s = st.text_input("Sigla", max_chars=3)
            nac = st.text_input("Nacionalidade")
            if st.form_submit_button("Salvar País"):
                if n:
                    PaisService.criar(nome=n, sigla=s, nacionalidade=nac)
                    st.success("País cadastrado com sucesso!")
                    st.rerun()

def renderizar_gerenciador_estados():
    """Nível 2: Popover de Estados"""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Estado", "➕ Novo Estado"])
    with tab_sel:
        e_list = EstadoService.listar_todos()
        if not e_list:
            st.info("Nenhum estado cadastrado.")
        else:
            data = [{ "id": e['id'], "Estado": e['nome'], "UF": e['uf']} for e in e_list]
            df_e = pd.DataFrame(data)
            evt = st.dataframe(df_e, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="grid_e_geo")
            if evt.selection.rows:
                idx = evt.selection.rows[0]
                escolhido = df_e.iloc[idx]
                st.session_state.estado_selecionado_geo = {"label": f"{escolhido['Estado']} ({escolhido['UF']})", "id": int(escolhido['id'])}
                st.rerun()
    with tab_cad:
        ne = st.text_input("Nome do Estado", key="txt_ne")
        ue = st.text_input("UF", max_chars=2, key="txt_ue").upper()
        p_atual = st.session_state.pais_selecionado_geo
        lbl_p = p_atual['label'] if p_atual else "Selecionar País..."
        
        st.write("**País Pertencente**")
        with st.popover(lbl_p, icon="🌎", use_container_width=True):
            renderizar_gerenciador_paises()
            
        if st.button("Salvar Estado", type="primary", key="btn_se"):
            if ne and ue and p_atual:
                EstadoService.criar(ne, ue, p_atual['id'])
                st.success("Estado cadastrado com sucesso!")
                st.session_state.pais_selecionado_geo = None
                st.rerun()
            else:
                st.error("Preencha Nome, UF e o País.")

@st.dialog("Gerenciar Cidades", width="large")
def gerenciar_cidades_modal():
    """Nível 1: Modal Principal de Cidades"""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Cidade", "➕ Nova Cidade"])
    with tab_sel:
        c_list = CidadeService.listar_todos()
        if not c_list:
            st.info("Nenhuma cidade cadastrada.")
        else:
            data = [{"id": c['id'], "Cidade": c['nome'], "UF": c.get('estado', {}).get('uf', 'N/A') } for c in c_list]
            df_c = pd.DataFrame(data)
            evt = st.dataframe(df_c, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="grid_c_geo")
            if evt.selection.rows:
                idx = evt.selection.rows[0]
                escolhido = df_c.iloc[idx]
                # Salva diretamente o ID e a Label no estado global
                st.session_state.cidade_selecionada_cliente = {
                    "label": f"{escolhido['Cidade']} - {escolhido['UF']}",
                    "id": int(escolhido['id'])
                }
                st.session_state.mostrar_dialog_cidades = False
                st.rerun()
    with tab_cad:
        nc = st.text_input("Nome da Cidade", key="txt_nc")
        ibge = st.text_input("Código IBGE", key="txt_ibge")
        e_atual = st.session_state.estado_selecionado_geo
        lbl_e = e_atual['label'] if e_atual else "Selecionar Estado..."
        
        st.write("**Estado Pertencente**")
        with st.popover(lbl_e, icon="📍", use_container_width=True):
            renderizar_gerenciador_estados()
            
        if st.button("Salvar Cidade", type="primary", key="btn_sc"):
            if nc and e_atual:
                res = CidadeService.criar(nc, ibge, e_atual['id'])
                try:
                    novo_id = res.data[0]['id'] if res.data else None
                except:
                    novo_id = None
                
                uf_extraida = e_atual['label'].split('(')[-1].replace(')', '').strip()
                st.session_state.cidade_selecionada_cliente = {
                    "label": f"{nc.strip().upper()} - {uf_extraida}",
                    "id": novo_id
                }
                st.session_state.estado_selecionado_geo = None
                st.session_state.mostrar_dialog_cidades = False
                st.rerun()
            else:
                st.error("Preencha o Nome e selecione o Estado.")

# Dispara o modal se a flag de visualização estiver ativa
if st.session_state.mostrar_dialog_cidades:
    gerenciar_cidades_modal()


# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.cliente_para_editar is not None
titulo_formulario = "✏️ Editar Cliente" if modo_edicao else "✨ Novo Cliente"

with st.expander(titulo_formulario, expanded=True):
    if modo_edicao:
        c = st.session_state.cliente_para_editar
        nome_padrao = c["cliente"]
        apelido_padrao = c["apelido"]
        cpf_padrao = c["cpf"]
        nasc_padrao = date.fromisoformat(c["data_nascimento"]) if c["data_nascimento"] else date.today()
        sexo_padrao_idx = ["M", "F"].index(c["sexo"]) if c["sexo"] in ["M", "F"] else 1
        cep_padrao = c["cep"] if c["cep"] else ""
        end_padrao = c["endereco"] if c["endereco"] else ""
        num_padrao = c["numero"] if c["numero"] else ""
        bairro_padrao = c["bairro"] if c["bairro"] else ""
        comp_padrao = c["complemento"] if c["complemento"] else ""
        email_padrao = c["email"] if c["email"] else ""
        tel_padrao = c["telefone"] if c["telefone"] else ""
        obs_padrao = c["observacao"] if c["observacao"] else ""
    else:
        nome_padrao = ""
        apelido_padrao = ""
        cpf_padrao = ""
        nasc_padrao = date.today()
        sexo_padrao_idx = 1
        cep_padrao = ""
        end_padrao = ""
        num_padrao = ""
        bairro_padrao = ""
        comp_padrao = ""
        email_padrao = ""
        tel_padrao = ""
        obs_padrao = ""

    col1, col2 = st.columns(2)
    nome = col1.text_input("Cliente*", placeholder="Ex: Maria Silva", value=nome_padrao)
    apelido = col2.text_input("Apelido", value=apelido_padrao)
    
    col3, col4, col5 = st.columns([0.4, 0.3, 0.1])
    cpf = col3.text_input("CPF (Somente números)*", value=cpf_padrao)
    nascimento = col4.date_input("Data de Nascimento", min_value=date(1920, 1, 1), max_value=date.today(), value=nasc_padrao)
    sexo = col5.selectbox("Sexo", options=["M", "F"], index=sexo_padrao_idx)

    col_cep, col_rua, col_num = st.columns([0.2, 0.6, 0.2])
    cep = col_cep.text_input("CEP", value=cep_padrao)
    endereco = col_rua.text_input("Rua/Logradouro", value=end_padrao)
    numero = col_num.text_input("Nº", value=num_padrao)
    
    # Colunas adaptadas: sem dropdown, usando uma caixa de texto travada (disabled)
    col_bairro, col_cidade, col_geo_btn = st.columns([0.4, 0.4, 0.2])
    bairro = col_bairro.text_input("Bairro", value=bairro_padrao)
    
    # Determina o texto de exibição do campo de Cidade
    c_atual = st.session_state.cidade_selecionada_cliente
    txt_cidade_exibicao = c_atual["label"] if c_atual else "Nenhuma selecionada..."
    
    # Campo alterado de selectbox para text_input travado
    col_cidade.text_input("Cidade/UF*", value=txt_cidade_exibicao, disabled=True, help="Use o botão ao lado para escolher")
    
    col_geo_btn.write("") 
    col_geo_btn.write("") 
    if col_geo_btn.button("🔍 Buscar / Criar", use_container_width=True, type="secondary"):
        st.session_state.mostrar_dialog_cidades = True
        st.rerun()

    complemento = st.text_input("Complemento", value=comp_padrao)
    
    col6, col7 = st.columns(2)
    email = col6.text_input("E-mail", value=email_padrao)
    telefone_cliente = col7.text_input("Telefone", key="input_telefone", value=tel_padrao)
    observacao = st.text_area("Preferências ou Observações", value=obs_padrao)

    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.15, 0.15, 0.7])
    
    novo_cliente = {
        "cliente": nome, "apelido": apelido, "cpf": cpf, "email": email, "telefone": telefone_cliente, 
        "data_nascimento": str(nascimento), "sexo": sexo, "cep": cep, "endereco": endereco, "numero": numero, 
        "bairro": bairro, "complemento": complemento, 
        "cidade_id": c_atual["id"] if c_atual else None,  # Pega o ID diretamente do Session State
        "observacao": observacao
    }

    if modo_edicao:
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if not nome or not cpf: st.error("Campos com * são obrigatórios.")
            elif not c_atual: st.error("Selecione uma Cidade válida.")
            elif not validar_cpf(cpf): st.error("CPF inválido! Verifique os números.")
            else:
                ClienteService.editar(st.session_state.cliente_para_editar["id"], novo_cliente)
                st.success("Cliente atualizado com sucesso!")
                st.session_state.cliente_para_editar = None
                st.session_state.cidade_selecionada_cliente = None
                st.rerun()
                
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.cliente_para_editar = None
            st.session_state.cidade_selecionada_cliente = None
            st.rerun()
    else:
        if col_btn_salvar.button("Salvar Cliente", type="primary", use_container_width=True):
            if not nome or not cpf: st.error("Campos com * são obrigatórios.")
            elif not c_atual: st.error("Selecione uma Cidade válida antes de salvar.")
            elif not validar_cpf(cpf): st.error("CPF inválido! Verifique os números.")
            else:
                try:
                    ClienteService.criar(novo_cliente)
                    st.success(f"Cliente {nome} cadastrado com sucesso!")
                    st.session_state.cidade_selecionada_cliente = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no Supabase: {e}")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativados = st.checkbox("👁️ Exibir clientes desativados (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
clientes = ClienteService.listar_todos(apenas_ativos=not exibir_desativados)

if clientes:
    st.subheader("📊 Clientes Cadastrados")
    dados_grid = []
    for c in clientes:
        cid_rel = c.get('cidade', {})
        est_rel = cid_rel.get('estado', {}) if cid_rel else {}
        dados_grid.append({
            "id": c['id'], "Nome": c['cliente'], "Apelido": c.get('apelido', ''), "CPF": c['cpf'],
            "Telefone": c.get('telefone', ''), "E-mail": c.get('email', ''),
            "Cidade": f"{cid_rel['nome']} - {est_rel['uf']}" if cid_rel and est_rel else "N/A",
            "cidade_id": cid_rel.get('id') if cid_rel else None, # Guardado em background
            "Status": "🟢 Ativo" if c.get('ativo', True) else "🔴 Desativado",
            "data_nascimento": c.get('data_nascimento'), "sexo": c.get('sexo'), "cep": c.get('cep'),
            "endereco": c.get('endereco'), "numero": c.get('numero'), "bairro": c.get('bairro'),
            "complemento": c.get('complemento'), "observacao": c.get('observacao')
        })
        
    df_clientes = pd.DataFrame(dados_grid)
    evento_grid = st.dataframe(
        df_clientes,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "cidade_id": None, # Mantém oculto no grid
            "data_nascimento": None, "sexo": None, "cep": None, "endereco": None, 
            "numero": None, "bairro": None, "complemento": None, "observacao": None,
            "Nome": st.column_config.TextColumn("Nome", width="large"),
            "Cidade": st.column_config.TextColumn("Cidade", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True, hide_index=True, selection_mode="single-row", on_select="rerun"
    )
    
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        cliente_escolhido = df_clientes.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{cliente_escolhido['id']}** - **{cliente_escolhido['Nome']}**")
        
        if c_edit.button("✏️ Editar Selecionado", use_container_width=True):
            st.session_state.cliente_para_editar = {
                "id": int(cliente_escolhido['id']), "cliente": cliente_escolhido['Nome'], "apelido": cliente_escolhido['Apelido'],
                "cpf": cliente_escolhido['CPF'], "telefone": cliente_escolhido['Telefone'], "email": cliente_escolhido['E-mail'],
                "data_nascimento": cliente_escolhido['data_nascimento'], "sexo": cliente_escolhido['sexo'], "cep": cliente_escolhido['cep'],
                "endereco": cliente_escolhido['endereco'], "numero": cliente_escolhido['numero'], "bairro": cliente_escolhido['bairro'],
                "complemento": cliente_escolhido['complemento'], "observacao": cliente_escolhido['observacao']
            }
            # Popula o estado com a cidade vinda do Grid de Clientes
            st.session_state.cidade_selecionada_cliente = {
                "label": cliente_escolhido['Cidade'],
                "id": int(cliente_escolhido['cidade_id']) if pd.notna(cliente_escolhido['cidade_id']) else None
            }
            st.rerun()
            
        esta_ativo = "🟢 Ativo" in cliente_escolhido['Status']
        texto_botao = "❌ Desativar" if esta_ativo else "🔄 Reativar"
        if c_del.button(texto_botao, type="primary" if esta_ativo else "secondary", use_container_width=True):
            ClienteService.alternar_status(int(cliente_escolhido['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("Nenhum cliente localizado com os filtros aplicados.")