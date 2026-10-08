import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from supabase import Client, create_client


from services.condicaopag_service import CondicaoPagamentoService
from services.cidade_service import CidadeService
from services.estado_service import EstadoService
from services.fornecedor_service import FornecedorService
from services.pais_service import PaisService

# Carrega variáveis de ambiente (.env)
load_dotenv()


@st.cache_resource
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        st.error(
            "As variáveis SUPABASE_URL e SUPABASE_KEY não foram encontradas no"
            " .env."
        )
        st.stop()

    return create_client(url, key)


supabase = init_supabase()
service = FornecedorService(supabase)

st.set_page_config(page_title="Novo Fornecedor", layout="wide")

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "cidade_fornecedor_selecionada" not in st.session_state:
    st.session_state.cidade_fornecedor_selecionada = None

if "estado_fornecedor_selecionado" not in st.session_state:
    st.session_state.estado_fornecedor_selecionado = None

if "pais_fornecedor_selecionado" not in st.session_state:
    st.session_state.pais_fornecedor_selecionado = None

if "emails" not in st.session_state:
    st.session_state.emails = []

if "telefones" not in st.session_state:
    st.session_state.telefones = []

# --- CARREGAR CONDIÇÕES DE PAGAMENTO DO BANCO DE DADOS ---
condicoes_db = CondicaoPagamentoService.listar_todas(apenas_ativos=True)
opcoes_condicao_pagamento = (
    [
        cp["condicao_pagamento"]
        for cp in condicoes_db
        if cp.get("condicao_pagamento")
    ]
    if condicoes_db
    else ["A VISTA", "30 DIAS", "30/60 DIAS"]
)


# --- COMPONENTES AUXILIARES DE LOCALIZAÇÃO (POPOVERS) ---


def renderizar_gerenciador_paises(prefix="padrao"):
    """Gerenciador de Países dentro de Popovers."""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar País", "➕ Novo País"])

    with tab_sel:
        exibir_desat = st.checkbox(
            "👁️ Exibir desativados", value=False, key=f"{prefix}_chk_p_desat"
        )
        paises = PaisService.listar_todos(apenas_ativos=not exibir_desat)

        if not paises:
            st.info("Nenhum país cadastrado.")
        else:
            dados_p = [
                {
                    "id": p["id"],
                    "País": p["nome"],
                    "Sigla": p.get("sigla", ""),
                    "Nacionalidade": p.get("nacionalidade", ""),
                    "Status": (
                        "🟢 Ativo" if p.get("ativo", True) else "🔴 Desativado"
                    ),
                }
                for p in paises
            ]
            df_p = pd.DataFrame(dados_p)
            event = st.dataframe(
                df_p,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key=f"{prefix}_grid_paises",
            )

            if event.selection.rows:
                idx = event.selection.rows[0]
                escolhido = df_p.iloc[idx]

                if escolhido["Status"] == "🟢 Ativo":
                    if st.button(
                        "🎯 Selecionar País",
                        use_container_width=True,
                        key=f"{prefix}_btn_sel_p",
                    ):
                        st.session_state.pais_fornecedor_selecionado = {
                            "id": int(escolhido["id"]),
                            "label": escolhido["País"],
                        }
                        st.rerun()

    with tab_cad:
        with st.form(f"{prefix}_form_novo_pais", clear_on_submit=True):
            c1, c2 = st.columns(2)
            n_pais = c1.text_input("Nome do País")
            s_pais = c2.text_input("Sigla", max_chars=3)
            nacionalidade = st.text_input("Nacionalidade")
            if st.form_submit_button("Salvar País"):
                if n_pais:
                    PaisService.criar(
                        nome=n_pais, sigla=s_pais, nacionalidade=nacionalidade
                    )
                    st.success("País cadastrado!")
                    st.rerun()
                else:
                    st.error("Informe o nome do país.")


def renderizar_gerenciador_estados(prefix="padrao"):
    """Gerenciador de Estados dentro de Popovers."""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Estado", "➕ Novo Estado"])

    with tab_sel:
        exibir_desat = st.checkbox(
            "👁️ Exibir desativados", value=False, key=f"{prefix}_chk_e_desat"
        )
        estados = EstadoService.listar_todos(apenas_ativos=not exibir_desat)

        if not estados:
            st.info("Nenhum estado cadastrado.")
        else:
            data = []
            for e in estados:
                p = e.get("pais") if isinstance(e.get("pais"), dict) else {}
                data.append({
                    "id": e["id"],
                    "Estado": e["nome"],
                    "UF": e["uf"],
                    "País": p.get("nome", "N/A") if p else "N/A",
                    "pais_id": e.get("pais_id"),
                    "Status": (
                        "🟢 Ativo" if e.get("ativo", True) else "🔴 Desativado"
                    ),
                })
            df_e = pd.DataFrame(data)
            event = st.dataframe(
                df_e,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key=f"{prefix}_grid_estados",
            )

            if event.selection.rows:
                idx = event.selection.rows[0]
                escolhido = df_e.iloc[idx]

                if escolhido["Status"] == "🟢 Ativo":
                    if st.button(
                        "🎯 Selecionar Estado",
                        use_container_width=True,
                        key=f"{prefix}_btn_sel_e",
                    ):
                        st.session_state.estado_fornecedor_selecionado = {
                            "id": int(escolhido["id"]),
                            "label": (
                                f"{escolhido['Estado']} ({escolhido['UF']})"
                            ),
                        }
                        if escolhido["País"] != "N/A":
                            st.session_state.pais_fornecedor_selecionado = {
                                "id": (
                                    int(escolhido["pais_id"])
                                    if pd.notna(escolhido.get("pais_id"))
                                    else None
                                ),
                                "label": escolhido["País"],
                            }
                        st.rerun()

    with tab_cad:
        with st.container(border=True):
            st.write("##### Novo Estado")
            nome_e = st.text_input("Nome do Estado", key=f"{prefix}_cad_e_nome")
            uf_e = st.text_input(
                "UF", max_chars=2, key=f"{prefix}_cad_e_uf"
            ).upper()

            p_atual = st.session_state.pais_fornecedor_selecionado
            txt_p = p_atual["label"] if p_atual else "Selecionar País..."

            st.write("**País Pertencente**")
            with st.popover(txt_p, icon="🌎", use_container_width=True):
                renderizar_gerenciador_paises(prefix=f"{prefix}_nest_p")

            if st.button(
                "Salvar Estado",
                type="primary",
                use_container_width=True,
                key=f"{prefix}_btn_save_e",
            ):
                if nome_e and uf_e and p_atual:
                    EstadoService.criar(nome_e, uf_e, p_atual["id"])
                    st.success("Estado cadastrado!")
                    st.rerun()
                else:
                    st.error("Preencha Nome, UF e selecione o País.")


@st.dialog("Gerenciar Cidades", width="large")
def gerenciar_cidades_modal():
    """Modal Principal para selecionar ou cadastrar Cidades, Estados e Países."""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Cidade", "➕ Nova Cidade"])

    with tab_sel:
        exibir_desat = st.checkbox(
            "👁️ Exibir cidades desativadas", value=False, key="chk_c_desat"
        )
        cidades = CidadeService.listar_todos(apenas_ativos=not exibir_desat)

        if not cidades:
            st.info("Nenhuma cidade cadastrada.")
        else:
            data = []
            for c in cidades:
                est = c.get("estado") or {}
                pais = est.get("pais") or {} if isinstance(est, dict) else {}
                nome_pais = (
                    pais.get("nome", "N/A") if isinstance(pais, dict) else "N/A"
                )

                data.append({
                    "id": c["id"],
                    "Cidade": c["nome"],
                    "Estado": (
                        est.get("nome", "N/A")
                        if isinstance(est, dict)
                        else "N/A"
                    ),
                    "UF": (
                        est.get("uf", "N/A") if isinstance(est, dict) else "N/A"
                    ),
                    "País": nome_pais,
                    "Status": (
                        "🟢 Ativo" if c.get("ativo", True) else "🔴 Desativado"
                    ),
                })
            df_c = pd.DataFrame(data)
            event = st.dataframe(
                df_c,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="grid_cidades_modal",
            )

            if event.selection.rows:
                idx = event.selection.rows[0]
                escolhida = df_c.iloc[idx]

                if escolhida["Status"] == "🟢 Ativo":
                    if st.button(
                        "🎯 Selecionar Cidade para Fornecedor",
                        type="primary",
                        use_container_width=True,
                        key="btn_sel_cidade_fornecedor",
                    ):
                        st.session_state.cidade_fornecedor_selecionada = {
                            "id": int(escolhida["id"]),
                            "nome": escolhida["Cidade"],
                            "estado": f"{escolhida['Estado']} ({escolhida['UF']})",
                            "pais": escolhida["País"],
                        }
                        st.rerun()

    with tab_cad:
        with st.container(border=True):
            st.write("##### Nova Cidade")
            nome_c = st.text_input("Nome da Cidade", key="cad_cidade_nome")

            e_atual = st.session_state.estado_fornecedor_selecionado
            txt_e = e_atual["label"] if e_atual else "Selecionar Estado..."

            st.write("**Estado Pertencente**")
            with st.popover(txt_e, icon="📍", use_container_width=True):
                renderizar_gerenciador_estados(prefix="cad_cidade_nest_e")

            if st.button(
                "Salvar Cidade",
                type="primary",
                use_container_width=True,
                key="btn_save_cidade",
            ):
                if nome_c and e_atual:
                    res = CidadeService.criar(
                        nome=nome_c, estado_id=e_atual["id"]
                    )
                    st.success("Cidade cadastrada!")

                    p_sel = st.session_state.pais_fornecedor_selecionado
                    pais_nome = p_sel["label"] if p_sel else "N/A"

                    st.session_state.cidade_fornecedor_selecionada = {
                        "id": res.get("id") if isinstance(res, dict) else None,
                        "nome": nome_c,
                        "estado": e_atual["label"],
                        "pais": pais_nome,
                    }
                    st.rerun()
                else:
                    st.error("Informe o Nome da Cidade e selecione o Estado.")


# --- TELA PRINCIPAL: FORMULÁRIO DE CADASTRO DE FORNECEDOR ---

st.caption("Fornecedores / Novo Fornecedor")
st.title("Novo Fornecedor")

cidade_sel = st.session_state.cidade_fornecedor_selecionada

with st.form("form_fornecedor", clear_on_submit=False):

    # Tipo de Pessoa e Status
    col_tipo, col_status, col_empty = st.columns([2, 1, 5])
    with col_tipo:
        tipo_pessoa = st.selectbox("Tipo de Pessoa *", ["Jurídica", "Física"])
    with col_status:
        st.write("Status")
        status = st.toggle("Ativo", value=True)

    # Razão Social e Nome Fantasia
    col_razao, col_fantasia = st.columns([1, 1])
    with col_razao:
        razao_social = st.text_input(
            "Razão Social *", placeholder="Digite a razão social"
        )
    with col_fantasia:
        nome_fantasia = st.text_input(
            "Nome Fantasia", placeholder="Nome fantasia"
        )

    # CNPJ/CPF e Inscrição Estadual
    col_doc, col_ie = st.columns([1, 1])
    with col_doc:
        doc_label = "CNPJ *" if tipo_pessoa == "Jurídica" else "CPF *"
        doc_mask = (
            "00.000.000/0000-00"
            if tipo_pessoa == "Jurídica"
            else "000.000.000-00"
        )
        cnpj_cpf = st.text_input(doc_label, placeholder=doc_mask)
    with col_ie:
        inscricao_estadual = st.text_input(
            "Inscrição Estadual", placeholder="Número da I.E."
        )

    # CEP, Logradouro e Número
    col_cep, col_logradouro, col_num = st.columns([1.5, 3.5, 1])
    with col_cep:
        cep = st.text_input("CEP", placeholder="00000-000")
    with col_logradouro:
        logradouro = st.text_input(
            "Logradouro", placeholder="Rua, avenida, alameda..."
        )
    with col_num:
        numero = st.text_input("Número", placeholder="Nº")

    # Localização (País, Estado, Cidade)
    col_pais, col_uf, col_cidade, col_btn_geo = st.columns([1, 1, 1, 0.8])

    with col_pais:
        val_pais = (
            cidade_sel.get("pais", "Brasil") if cidade_sel else "Brasil"
        )
        pais = st.text_input("País *", value=val_pais)

    with col_uf:
        val_estado = cidade_sel.get("estado", "") if cidade_sel else ""
        estado = st.text_input(
            "Estado *", value=val_estado, placeholder="Ex: Alto Paraná (AP)"
        )

    with col_cidade:
        val_cidade = cidade_sel.get("nome", "") if cidade_sel else ""
        cidade = st.text_input(
            "Cidade *",
            value=val_cidade,
            placeholder="Selecione ou digite a cidade",
        )

    with col_btn_geo:
        st.write("**Localização**")
        btn_abrir_modal_geo = st.form_submit_button(
            "🏙️ Buscar / Criar", use_container_width=True
        )

    # Complemento e Bairro
    col_comp, col_bairro = st.columns([1, 1])
    with col_comp:
        complemento = st.text_input(
            "Complemento", placeholder="Apto, bloco, sala..."
        )
    with col_bairro:
        bairro = st.text_input("Bairro", placeholder="Bairro")

    # Condição de Pagamento (Carregada da tabela condicao_pagamento)
    col_cond, col_limite, col_transp = st.columns([1, 1, 1])
    with col_cond:
        condicao_pagamento = st.selectbox(
            "Condição de Pagamento *",
            options=opcoes_condicao_pagamento,
        )
    with col_limite:
        limite_credito = st.number_input(
            "Limite de Crédito (R$) *", min_value=0.0, value=0.0, step=100.0
        )
    with col_transp:
        transportadora = st.text_input(
            "Transportadora", placeholder="Selecionar uma transportadora..."
        )

    st.markdown("---")

    # Seção de E-mails
    st.subheader("E-MAILS")
    col_email_input, col_btn_email = st.columns([4, 1])
    with col_email_input:
        novo_email = st.text_input(
            "Adicionar E-mail",
            placeholder="exemplo@dominio.com",
            key="input_email",
        )

    if st.session_state.emails:
        for em in st.session_state.emails:
            st.text(f"• {em}")
    else:
        st.caption("Nenhum e-mail cadastrado.")

    # Seção de Telefones
    st.subheader("TELEFONES")
    col_tel_input, col_btn_tel = st.columns([4, 1])
    with col_tel_input:
        novo_tel = st.text_input(
            "Adicionar Telefone",
            placeholder="(00) 00000-0000",
            key="input_tel",
        )

    if st.session_state.telefones:
        for tel in st.session_state.telefones:
            st.text(f"• {tel}")
    else:
        st.caption("Nenhum telefone cadastrado.")

    # Observações
    st.subheader("Observações")
    observacoes = st.text_area(
        "Observações adicionais",
        placeholder="Observações adicionais",
        height=100,
    )

    st.markdown("---")

    # Botões Finais
    col_b1, col_b2, col_salvar, col_cancelar = st.columns([5, 1, 1, 1])
    with col_salvar:
        btn_salvar = st.form_submit_button(
            "Salvar", type="primary", use_container_width=True
        )
    with col_cancelar:
        btn_cancelar = st.form_submit_button(
            "Cancelar", use_container_width=True
        )

# Ação para abrir o modal de seleção geográfica
if btn_abrir_modal_geo:
    gerenciar_cidades_modal()

# Lógica de Gravação no Supabase
if btn_salvar:
    if novo_email and novo_email not in st.session_state.emails:
        st.session_state.emails.append(novo_email)
    if novo_tel and novo_tel not in st.session_state.telefones:
        st.session_state.telefones.append(novo_tel)

    if not razao_social or not cnpj_cpf or not cidade:
        st.error(
            "Por favor, preencha todos os campos obrigatórios marcados com (*)."
        )
    else:
        dados = {
            "tipo_pessoa": tipo_pessoa,
            "status": status,
            "razao_social": razao_social,
            "nome_fantasia": nome_fantasia,
            "cnpj_cpf": cnpj_cpf,
            "inscricao_estadual": inscricao_estadual,
            "cep": cep,
            "logradouro": logradouro,
            "numero": numero,
            "pais": pais,
            "estado": estado,
            "cidade": cidade,
            "cidade_id": (
                cidade_sel["id"] if cidade_sel and "id" in cidade_sel else None
            ),
            "complemento": complemento,
            "bairro": bairro,
            "condicao_pagamento": condicao_pagamento,
            "limite_credito": limite_credito,
            "transportadora": transportadora,
            "emails": st.session_state.emails,
            "telefones": st.session_state.telefones,
            "observacoes": observacoes,
        }

        sucesso, resultado = service.criar(dados)

        if sucesso:
            st.success("Fornecedor cadastrado com sucesso!")
            st.session_state.emails = []
            st.session_state.telefones = []
            st.session_state.cidade_fornecedor_selecionada = None
        else:
            st.error(f"Erro ao salvar fornecedor: {resultado}")

if btn_cancelar:
    st.info("Cadastro cancelado.")
    st.session_state.emails = []
    st.session_state.telefones = []
    st.session_state.cidade_fornecedor_selecionada = None