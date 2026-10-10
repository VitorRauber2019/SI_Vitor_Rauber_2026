import datetime
import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from supabase import Client, create_client

from services.categoria_service import CategoriaService
from services.cidade_service import CidadeService
from services.compra_service import CompraService
from services.condicaopag_service import CondicaoPagamentoService
from services.estado_service import EstadoService
from services.fornecedor_service import FornecedorService
from services.marca_service import MarcaService
from services.pais_service import PaisService
from services.produto_service import ProdutoService
from services.transportadora_service import TransportadoraService
from services.unidade_medida_service import UnidadeMedidaService
from utils.inputs import aplicar_padrao_inputs

# Carrega variáveis de ambiente (.env)
load_dotenv()

@st.cache_resource
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        st.error(
            "As variáveis SUPABASE_URL e SUPABASE_KEY não foram encontradas no .env."
        )
        st.stop()

    return create_client(url, key)

supabase = init_supabase()
compra_service = CompraService(supabase)
fornecedor_service = FornecedorService(supabase)
transp_service = TransportadoraService(supabase)

st.set_page_config(page_title="Cadastro de Compra", layout="wide")
aplicar_padrao_inputs()

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "fornecedor_compra_selecionado" not in st.session_state:
    st.session_state.fornecedor_compra_selecionado = None

if "transportadora_compra_selecionada" not in st.session_state:
    st.session_state.transportadora_compra_selecionada = None

if "itens_compra" not in st.session_state:
    st.session_state.itens_compra = []

# Normaliza itens que possam estar na sessão num formato antigo (ex.: campo "desconto")
st.session_state.itens_compra = [
    {
        "produto_id": int(i["produto_id"]),
        "produto": i.get("produto", ""),
        "quantidade": int(i.get("quantidade") or 1),
        "preco_unitario": float(i.get("preco_unitario") or 0),
        "desconto_percentual": float(i.get("desconto_percentual") or 0),
        "desconto_valor": float(i.get("desconto_valor", i.get("desconto")) or 0),
    }
    for i in st.session_state.itens_compra
    if i.get("produto_id") is not None
]

if "parcelas_compra" not in st.session_state:
    st.session_state.parcelas_compra = []

if "nota_confirmada" not in st.session_state:
    st.session_state.nota_confirmada = False

if "condicao_compra_sel" not in st.session_state:
    st.session_state.condicao_compra_sel = None

if "assinatura_parcelas" not in st.session_state:
    st.session_state.assinatura_parcelas = None

# Contadores usados nas keys dos widgets para reiniciá-los
if "versao_editor_itens" not in st.session_state:
    st.session_state.versao_editor_itens = 0

if "versao_form_compra" not in st.session_state:
    st.session_state.versao_form_compra = 0

# Localização usada nos cadastros rápidos de Fornecedor ("forn") e Transportadora ("transp")
for _alvo in ("forn", "transp"):
    for _campo in ("cidade", "estado", "pais"):
        if f"{_campo}_{_alvo}_compra" not in st.session_state:
            st.session_state[f"{_campo}_{_alvo}_compra"] = None

# --- CARREGAR DADOS AUXILIARES ---
condicoes_db = CondicaoPagamentoService.listar_todas(apenas_ativos=True)
opcoes_condicao_pagamento = (
    [
        cp["condicao_pagamento"]
        for cp in condicoes_db
        if cp.get("condicao_pagamento")
    ]
    if condicoes_db
    else ["À vista", "30 DIAS", "30/60 DIAS"]
)
condicoes_por_nome = {cp["condicao_pagamento"]: cp for cp in condicoes_db or []}

# --- COMPONENTES AUXILIARES DE LOCALIZAÇÃO (USADOS DENTRO DOS MODAIS) ---
# Os botões usam st.rerun(scope="fragment") para não fechar o modal (st.dialog) aberto.


def renderizar_gerenciador_paises(prefix, alvo):
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
                    "Status": "🟢 Ativo" if p.get("ativo", True) else "🔴 Desativado",
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
                escolhido = df_p.iloc[event.selection.rows[0]]

                if escolhido["Status"] == "🟢 Ativo":
                    if st.button("🎯 Selecionar País", use_container_width=True, key=f"{prefix}_btn_sel_p"):
                        st.session_state[f"pais_{alvo}_compra"] = {
                            "id": int(escolhido["id"]),
                            "label": escolhido["País"],
                        }
                        st.rerun(scope="fragment")

    with tab_cad:
        with st.container(border=True):
            c1, c2 = st.columns(2)
            n_pais = c1.text_input("Nome do País", key=f"{prefix}_cad_p_nome")
            s_pais = c2.text_input("Sigla", max_chars=3, key=f"{prefix}_cad_p_sigla")
            nacionalidade = st.text_input("Nacionalidade", key=f"{prefix}_cad_p_nac")
            if st.button("Salvar País", key=f"{prefix}_btn_save_p"):
                if n_pais:
                    PaisService.criar(nome=n_pais, sigla=s_pais, nacionalidade=nacionalidade)
                    st.success("País cadastrado!")
                    st.rerun(scope="fragment")
                else:
                    st.error("Informe o nome do país.")


def renderizar_gerenciador_estados(prefix, alvo):
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
                    "Status": "🟢 Ativo" if e.get("ativo", True) else "🔴 Desativado",
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
                escolhido = df_e.iloc[event.selection.rows[0]]

                if escolhido["Status"] == "🟢 Ativo":
                    if st.button("🎯 Selecionar Estado", use_container_width=True, key=f"{prefix}_btn_sel_e"):
                        st.session_state[f"estado_{alvo}_compra"] = {
                            "id": int(escolhido["id"]),
                            "label": f"{escolhido['Estado']} ({escolhido['UF']})",
                        }
                        if escolhido["País"] != "N/A":
                            st.session_state[f"pais_{alvo}_compra"] = {
                                "id": int(escolhido["pais_id"]) if pd.notna(escolhido.get("pais_id")) else None,
                                "label": escolhido["País"],
                            }
                        st.rerun(scope="fragment")

    with tab_cad:
        with st.container(border=True):
            st.write("##### Novo Estado")
            nome_e = st.text_input("Nome do Estado", key=f"{prefix}_cad_e_nome")
            uf_e = st.text_input("UF", max_chars=2, key=f"{prefix}_cad_e_uf").upper()

            p_atual = st.session_state[f"pais_{alvo}_compra"]
            txt_p = p_atual["label"] if p_atual else "Selecionar País..."

            st.write("**País Pertencente**")
            with st.popover(txt_p, icon="🌎", use_container_width=True):
                renderizar_gerenciador_paises(prefix=f"{prefix}_nest_p", alvo=alvo)

            if st.button("Salvar Estado", type="primary", use_container_width=True, key=f"{prefix}_btn_save_e"):
                if nome_e and uf_e and p_atual:
                    EstadoService.criar(nome_e, uf_e, p_atual["id"])
                    st.success("Estado cadastrado!")
                    st.rerun(scope="fragment")
                else:
                    st.error("Preencha Nome, UF e selecione o País.")


def renderizar_gerenciador_cidades(prefix, alvo):
    """Gerenciador de Cidades dentro de Popovers."""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Cidade", "➕ Nova Cidade"])

    with tab_sel:
        exibir_desat = st.checkbox(
            "👁️ Exibir cidades desativadas", value=False, key=f"{prefix}_chk_c_desat"
        )
        cidades = CidadeService.listar_todos(apenas_ativos=not exibir_desat)

        if not cidades:
            st.info("Nenhuma cidade cadastrada.")
        else:
            data = []
            for c in cidades:
                est = c.get("estado") or {}
                pais = est.get("pais") or {} if isinstance(est, dict) else {}
                data.append({
                    "id": c["id"],
                    "Cidade": c["nome"],
                    "Estado": (
                        f"{est.get('nome', 'N/A')} ({est.get('uf', 'N/A')})"
                        if isinstance(est, dict)
                        else "N/A"
                    ),
                    "País": pais.get("nome", "N/A") if isinstance(pais, dict) else "N/A",
                    "Status": "🟢 Ativo" if c.get("ativo", True) else "🔴 Desativado",
                })
            df_c = pd.DataFrame(data)
            event = st.dataframe(
                df_c,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key=f"{prefix}_grid_cidades",
            )

            if event.selection.rows:
                escolhida = df_c.iloc[event.selection.rows[0]]

                if escolhida["Status"] == "🟢 Ativo":
                    if st.button(
                        "🎯 Selecionar Cidade",
                        type="primary",
                        use_container_width=True,
                        key=f"{prefix}_btn_sel_cidade",
                    ):
                        st.session_state[f"cidade_{alvo}_compra"] = {
                            "id": int(escolhida["id"]),
                            "nome": escolhida["Cidade"],
                            "estado": escolhida["Estado"],
                            "pais": escolhida["País"],
                        }
                        st.rerun(scope="fragment")

    with tab_cad:
        with st.container(border=True):
            st.write("##### Nova Cidade")
            nome_c = st.text_input("Nome da Cidade", key=f"{prefix}_cad_cidade_nome")

            e_atual = st.session_state[f"estado_{alvo}_compra"]
            txt_e = e_atual["label"] if e_atual else "Selecionar Estado..."

            st.write("**Estado Pertencente**")
            with st.popover(txt_e, icon="📍", use_container_width=True):
                renderizar_gerenciador_estados(prefix=f"{prefix}_nest_e", alvo=alvo)

            if st.button("Salvar Cidade", type="primary", use_container_width=True, key=f"{prefix}_btn_save_cidade"):
                if nome_c and e_atual:
                    res = CidadeService.criar(nome=nome_c, estado_id=e_atual["id"])
                    p_sel = st.session_state[f"pais_{alvo}_compra"]
                    st.session_state[f"cidade_{alvo}_compra"] = {
                        "id": res.get("id") if isinstance(res, dict) else None,
                        "nome": nome_c,
                        "estado": e_atual["label"],
                        "pais": p_sel["label"] if p_sel else "N/A",
                    }
                    st.rerun(scope="fragment")
                else:
                    st.error("Informe o Nome da Cidade e selecione o Estado.")


def campos_endereco_contato(prefix, alvo):
    """Campos de endereço, localização e condição comercial comuns a Fornecedor e Transportadora."""
    c_cep, c_log, c_num = st.columns([1.5, 3.5, 1])
    cep = c_cep.text_input("CEP", placeholder="00000-000", key=f"{prefix}_cep")
    logradouro = c_log.text_input("Logradouro", placeholder="Rua, avenida, alameda...", key=f"{prefix}_logradouro")
    numero = c_num.text_input("Número", placeholder="Nº", key=f"{prefix}_numero")

    # Sem key: o valor acompanha a cidade selecionada no popover
    cidade_sel = st.session_state[f"cidade_{alvo}_compra"]
    c_pais, c_uf, c_cid, c_btn_geo = st.columns([1, 1, 1, 0.8])
    pais = c_pais.text_input("País *", value=cidade_sel.get("pais", "Brasil") if cidade_sel else "Brasil")
    estado = c_uf.text_input("Estado *", value=cidade_sel.get("estado", "") if cidade_sel else "", placeholder="Ex: São Paulo (SP)")
    cidade = c_cid.text_input("Cidade *", value=cidade_sel.get("nome", "") if cidade_sel else "", placeholder="Selecione ou digite...")
    with c_btn_geo:
        st.write("**Localização**")
        with st.popover("Buscar/Criar", icon="🏙️", use_container_width=True):
            renderizar_gerenciador_cidades(prefix=f"{prefix}_geo", alvo=alvo)

    c_comp, c_bairro = st.columns(2)
    complemento = c_comp.text_input("Complemento", placeholder="Apto, bloco, sala...", key=f"{prefix}_complemento")
    bairro = c_bairro.text_input("Bairro", placeholder="Bairro", key=f"{prefix}_bairro")

    return {
        "cep": cep,
        "logradouro": logradouro,
        "numero": numero,
        "pais": pais,
        "estado": estado,
        "cidade": cidade,
        "cidade_id": cidade_sel.get("id") if cidade_sel else None,
        "complemento": complemento,
        "bairro": bairro,
    }


def gerar_parcelas(parcelas_condicao, data_base, total):
    """Monta as parcelas da compra a partir das parcelas cadastradas na condição de pagamento."""
    if not parcelas_condicao:
        return [{"Vencimento": data_base, "Forma": "", "Valor": round(total, 2)}]

    parcelas = []
    acumulado = 0.0
    for i, p in enumerate(parcelas_condicao):
        if i < len(parcelas_condicao) - 1:
            valor = round(total * float(p["percentual"]) / 100, 2)
        else:
            # A última parcela absorve a diferença de centavos
            valor = round(total - acumulado, 2)
        acumulado += valor
        parcelas.append({
            "Vencimento": data_base + datetime.timedelta(days=int(p["dias"])),
            "Forma": p.get("forma_pagamento_nome") or "",
            "Valor": valor,
        })
    return parcelas


def lista_por_linha(texto):
    """Converte um text_area (um item por linha) em lista."""
    return [linha.strip() for linha in texto.splitlines() if linha.strip()]


def limpar_localizacao(alvo):
    for campo in ("cidade", "estado", "pais"):
        st.session_state[f"{campo}_{alvo}_compra"] = None


# --- MODAIS DE SELEÇÃO E CADASTRO RÁPIDO (FORNECEDOR, TRANSPORTADORA E PRODUTO) ---

@st.dialog("Gerenciar Fornecedores", width="large")
def gerenciar_fornecedores_modal():
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Fornecedor", "➕ Novo Fornecedor"])

    with tab_sel:
        exibir_desat = st.checkbox("👁️ Exibir desativados", value=False, key="chk_f_desat")
        fornecedores = fornecedor_service.listar_todos(apenas_ativos=not exibir_desat)

        if not fornecedores:
            st.info("Nenhum fornecedor cadastrado.")
        else:
            data = [
                {
                    "ID": f["id"],
                    "Razão Social": f.get("razao_social", ""),
                    "Nome Fantasia": f.get("nome_fantasia", ""),
                    "CNPJ/CPF": f.get("cnpj_cpf", ""),
                    "Cidade": f.get("cidade", "N/A"),
                    "Condição Pagamento": f.get("condicao_pagamento", ""),
                    "Status": "🟢 Ativo" if f.get("status", True) else "🔴 Desativado",
                }
                for f in fornecedores
            ]
            df_f = pd.DataFrame(data)
            event = st.dataframe(
                df_f,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="grid_fornecedores_modal",
            )

            if event.selection.rows:
                idx = event.selection.rows[0]
                escolhido = df_f.iloc[idx]

                if escolhido["Status"] == "🟢 Ativo":
                    if st.button(
                        "🎯 Selecionar Fornecedor para Compra",
                        type="primary",
                        use_container_width=True,
                        key="btn_sel_forn_compra",
                    ):
                        st.session_state.fornecedor_compra_selecionado = {
                            "id": int(escolhido["ID"]),
                            "nome": escolhido["Razão Social"],
                            "cnpj_cpf": escolhido["CNPJ/CPF"],
                            "condicao_pagamento": escolhido["Condição Pagamento"],
                        }
                        st.rerun()

    with tab_cad:
        with st.container(border=True):
            st.write("##### Cadastrar Novo Fornecedor")

            c_tipo, c_status = st.columns([2, 1])
            f_tipo = c_tipo.selectbox("Tipo de Pessoa *", ["Jurídica", "Física"], key="cad_f_tipo")
            f_status = c_status.toggle("Ativo", value=True, key="cad_f_status")

            c_rs, c_nf = st.columns(2)
            f_razao = c_rs.text_input("Razão Social *", key="cad_f_razao")
            f_fantasia = c_nf.text_input("Nome Fantasia", key="cad_f_fantasia")

            c_doc, c_ie = st.columns(2)
            f_doc_label = "CNPJ *" if f_tipo == "Jurídica" else "CPF *"
            f_doc_mask = "00.000.000/0000-00" if f_tipo == "Jurídica" else "000.000.000-00"
            f_cnpj = c_doc.text_input(f_doc_label, placeholder=f_doc_mask, key="cad_f_doc")
            f_ie = c_ie.text_input("Inscrição Estadual", placeholder="Número da I.E.", key="cad_f_ie")

            f_endereco = campos_endereco_contato(prefix="cad_f", alvo="forn")

            transportadoras_ativas = transp_service.listar_todos(apenas_ativos=True) or []
            opcoes_transp = {"Sem transportadora": None}
            opcoes_transp.update({t["razao_social"]: t["id"] for t in transportadoras_ativas if t.get("razao_social")})

            c_cond, c_lim, c_transp = st.columns(3)
            f_condicao = c_cond.selectbox("Condição de Pagamento *", options=opcoes_condicao_pagamento, key="cad_f_condicao")
            f_limite = c_lim.number_input("Limite de Crédito (R$) *", min_value=0.0, value=0.0, step=100.0, key="cad_f_limite")
            f_transp = c_transp.selectbox("Transportadora", options=list(opcoes_transp), key="cad_f_transp")

            c_em, c_tel = st.columns(2)
            f_emails = c_em.text_area("E-mails (um por linha)", placeholder="exemplo@dominio.com", key="cad_f_emails")
            f_telefones = c_tel.text_area("Telefones (um por linha)", placeholder="(00) 00000-0000", key="cad_f_telefones")

            f_obs = st.text_area("Observações", placeholder="Observações adicionais", key="cad_f_obs")

            if st.button("Salvar e Selecionar Fornecedor", type="primary", use_container_width=True, key="btn_save_forn_modal"):
                if f_razao and f_cnpj and f_endereco["cidade"]:
                    dados_f = {
                        "tipo_pessoa": f_tipo,
                        "status": f_status,
                        "razao_social": f_razao,
                        "nome_fantasia": f_fantasia,
                        "cnpj_cpf": f_cnpj,
                        "inscricao_estadual": f_ie,
                        **f_endereco,
                        "condicao_pagamento": f_condicao,
                        "limite_credito": f_limite,
                        "transportadora": f_transp if opcoes_transp[f_transp] else "",
                        "transportadora_id": opcoes_transp[f_transp],
                        "emails": lista_por_linha(f_emails),
                        "telefones": lista_por_linha(f_telefones),
                        "observacoes": f_obs,
                    }
                    sucesso, res = fornecedor_service.criar(dados_f)

                    if sucesso:
                        st.success("Fornecedor cadastrado com sucesso!")
                        st.session_state.fornecedor_compra_selecionado = {
                            "id": res.get("id") if isinstance(res, dict) else None,
                            "nome": f_razao,
                            "cnpj_cpf": f_cnpj,
                            "condicao_pagamento": f_condicao,
                        }
                        limpar_localizacao("forn")
                        st.rerun()
                    else:
                        st.error(f"Erro ao salvar fornecedor: {res}")
                else:
                    st.error("Preencha Razão Social, CNPJ/CPF e Cidade.")

@st.dialog("Gerenciar Transportadoras", width="large")
def gerenciar_transportadoras_modal():
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Transportadora", "➕ Nova Transportadora"])

    with tab_sel:
        exibir_desat = st.checkbox("👁️ Exibir desativadas", value=False, key="chk_t_desat")
        transportadoras = transp_service.listar_todos(apenas_ativos=not exibir_desat)

        if not transportadoras:
            st.info("Nenhuma transportadora cadastrada.")
        else:
            data = [
                {
                    "ID": t["id"],
                    "Razão Social": t.get("razao_social", ""),
                    "Nome Fantasia": t.get("nome_fantasia", ""),
                    "CNPJ/CPF": t.get("cnpj_cpf", ""),
                    "Cidade": t.get("cidade", "N/A"),
                    "Status": "🟢 Ativo" if t.get("status", True) else "🔴 Desativado",
                }
                for t in transportadoras
            ]
            df_t = pd.DataFrame(data)
            event = st.dataframe(
                df_t,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="grid_transportadoras_modal",
            )

            if event.selection.rows:
                idx = event.selection.rows[0]
                escolhida = df_t.iloc[idx]

                if escolhida["Status"] == "🟢 Ativo":
                    if st.button(
                        "🎯 Selecionar Transportadora para Compra",
                        type="primary",
                        use_container_width=True,
                        key="btn_sel_transp_compra",
                    ):
                        st.session_state.transportadora_compra_selecionada = {
                            "id": int(escolhida["ID"]),
                            "nome": escolhida["Razão Social"],
                        }
                        st.rerun()

    with tab_cad:
        with st.container(border=True):
            st.write("##### Cadastrar Nova Transportadora")

            c_tipo, c_status = st.columns([2, 1])
            t_tipo = c_tipo.selectbox("Tipo de Pessoa *", ["Jurídica", "Física"], key="cad_t_tipo")
            t_status = c_status.toggle("Ativo", value=True, key="cad_t_status")

            c_rs, c_nf = st.columns(2)
            t_razao = c_rs.text_input("Razão Social *", key="cad_t_razao")
            t_fantasia = c_nf.text_input("Nome Fantasia", key="cad_t_fantasia")

            c_doc, c_ie = st.columns(2)
            t_doc_label = "CNPJ *" if t_tipo == "Jurídica" else "CPF *"
            t_doc_mask = "00.000.000/0000-00" if t_tipo == "Jurídica" else "000.000.000-00"
            t_cnpj = c_doc.text_input(t_doc_label, placeholder=t_doc_mask, key="cad_t_doc")
            t_ie = c_ie.text_input("Inscrição Estadual", placeholder="Número da I.E.", key="cad_t_ie")

            t_endereco = campos_endereco_contato(prefix="cad_t", alvo="transp")

            c_cond, c_lim = st.columns(2)
            t_condicao = c_cond.selectbox("Condição de Pagamento *", options=opcoes_condicao_pagamento, key="cad_t_condicao")
            t_limite = c_lim.number_input("Limite de Crédito (R$) *", min_value=0.0, value=0.0, step=100.0, key="cad_t_limite")

            c_em, c_tel, c_veic = st.columns(3)
            t_emails = c_em.text_area("E-mails (um por linha)", placeholder="exemplo@dominio.com", key="cad_t_emails")
            t_telefones = c_tel.text_area("Telefones (um por linha)", placeholder="(00) 00000-0000", key="cad_t_telefones")
            t_veiculos = c_veic.text_area("Veículos (um por linha)", placeholder="Placa / Modelo / RNTRC", key="cad_t_veiculos")

            t_obs = st.text_area("Observações", placeholder="Observações adicionais", key="cad_t_obs")

            if st.button("Salvar e Selecionar Transportadora", type="primary", use_container_width=True, key="btn_save_transp_modal"):
                if t_razao and t_cnpj and t_endereco["cidade"]:
                    dados_t = {
                        "tipo_pessoa": t_tipo,
                        "status": t_status,
                        "razao_social": t_razao,
                        "nome_fantasia": t_fantasia,
                        "cnpj_cpf": t_cnpj,
                        "inscricao_estadual": t_ie,
                        **t_endereco,
                        "condicao_pagamento": t_condicao,
                        "limite_credito": t_limite,
                        "emails": lista_por_linha(t_emails),
                        "telefones": lista_por_linha(t_telefones),
                        "veiculos": lista_por_linha(t_veiculos),
                        "observacoes": t_obs,
                    }
                    sucesso, res = transp_service.criar(dados_t)

                    if sucesso:
                        st.success("Transportadora cadastrada com sucesso!")
                        st.session_state.transportadora_compra_selecionada = {
                            "id": res.get("id") if isinstance(res, dict) and res.get("id") else None,
                            "nome": t_razao,
                        }
                        limpar_localizacao("transp")
                        st.rerun()
                    else:
                        st.error(f"Erro ao salvar transportadora: {res}")
                else:
                    st.error("Preencha Razão Social, CNPJ/CPF e Cidade.")


# --- FUNÇÕES DE CÁLCULO DA COMPRA ---


def moeda(valor):
    """Formata um número no padrão R$ 1.234,56."""
    return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def calcular_itens(itens, custos_adicionais):
    """Calcula total, rateio das despesas (frete + seguro + outras) e custo unitário de cada item."""
    calculados = []
    for item in itens:
        bruto = item["quantidade"] * item["preco_unitario"]
        total = round(bruto - item["desconto_valor"], 2)
        calculados.append({**item, "total_item": total})

    total_produtos = sum(i["total_item"] for i in calculados)
    acumulado = 0.0
    for idx, item in enumerate(calculados):
        if total_produtos <= 0:
            rateio = 0.0
        elif idx < len(calculados) - 1:
            rateio = round(custos_adicionais * item["total_item"] / total_produtos, 2)
        else:
            # O último item absorve a diferença de centavos do rateio
            rateio = round(custos_adicionais - acumulado, 2)
        acumulado += rateio
        item["custo_rateio"] = rateio
        item["custo_unitario"] = round((item["total_item"] + rateio) / item["quantidade"], 4)
    return calculados


def adicionar_item(produto_id, produto, quantidade, preco_unitario, desconto_percentual, desconto_valor):
    """Adiciona o produto à compra (ou soma a quantidade se ele já estiver na lista)."""
    for item in st.session_state.itens_compra:
        if item["produto_id"] == produto_id:
            item["quantidade"] += quantidade
            item["preco_unitario"] = preco_unitario
            bruto = item["quantidade"] * preco_unitario
            item["desconto_percentual"] = desconto_percentual
            item["desconto_valor"] = round(bruto * desconto_percentual / 100, 2) if desconto_percentual else desconto_valor
            break
    else:
        st.session_state.itens_compra.append({
            "produto_id": produto_id,
            "produto": produto,
            "quantidade": quantidade,
            "preco_unitario": preco_unitario,
            "desconto_percentual": desconto_percentual,
            "desconto_valor": desconto_valor,
        })
    st.session_state.versao_editor_itens += 1


def limpar_compra():
    """Descarta a compra em digitação e volta para a etapa 1."""
    st.session_state.fornecedor_compra_selecionado = None
    st.session_state.transportadora_compra_selecionada = None
    st.session_state.itens_compra = []
    st.session_state.parcelas_compra = []
    st.session_state.nota_confirmada = False
    st.session_state.condicao_compra_sel = None
    st.session_state.assinatura_parcelas = None
    st.session_state.versao_editor_itens += 1
    st.session_state.versao_form_compra += 1


# --- POPUPS DE PRODUTO E CONDIÇÃO DE PAGAMENTO ---


@st.dialog("Consultar Produto", width="large")
def consultar_produto_modal():
    tab_cons, tab_cad = st.tabs(["🔍 Consultar Produto", "➕ Cadastrar Produto"])

    with tab_cons:
        c_tipo, c_busca = st.columns([1, 3])
        tipo_busca = c_tipo.selectbox(
            "Buscar por", ["Descrição", "Referência (ID)", "Código de barras"], key="prod_tipo_busca"
        )
        termo = c_busca.text_input("Pesquisa", placeholder="Digite para filtrar...", key="prod_termo_busca").strip()

        produtos = ProdutoService.listar_todos(apenas_ativos=True) or []
        if termo:
            termo_l = termo.lower()
            if tipo_busca == "Referência (ID)":
                produtos = [p for p in produtos if str(p["id"]) == termo]
            elif tipo_busca == "Código de barras":
                produtos = [p for p in produtos if termo_l in str(p.get("codigo_barras") or "").lower()]
            else:
                produtos = [p for p in produtos if termo_l in str(p.get("produto") or "").lower()]

        if not produtos:
            st.info("Nenhum produto encontrado.")
            return

        df_prod = pd.DataFrame([
            {
                "Ref.": p["id"],
                "Produto": p.get("produto", ""),
                "Código de Barras": p.get("codigo_barras") or "",
                "UN": (p.get("unidade_medida") or {}).get("sigla", ""),
                "Estoque": p.get("quantidade_atual", 0),
                "Valor Compra": float(p.get("valor_compra") or 0),
            }
            for p in produtos
        ])
        event = st.dataframe(
            df_prod,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="grid_consulta_produtos",
            column_config={"Valor Compra": st.column_config.NumberColumn(format="R$ %.2f")},
        )

        if not event.selection.rows:
            st.caption("Selecione um produto para ver os detalhes e adicionar à compra.")
            return

        prod = produtos[event.selection.rows[0]]

        with st.container(border=True):
            st.write(f"##### {prod['id']} – {prod.get('produto', '')}")
            d1, d2, d3, d4 = st.columns(4)
            d1.write(f"**Marca:** {(prod.get('marca') or {}).get('marca', 'N/A')}")
            d2.write(f"**Categoria:** {(prod.get('categoria') or {}).get('categoria', 'N/A')}")
            d3.write(f"**Unidade:** {(prod.get('unidade_medida') or {}).get('sigla', 'N/A')}")
            d4.write(f"**Estoque atual:** {prod.get('quantidade_atual', 0)}")
            d5, d6, d7 = st.columns([1, 1, 2])
            d5.write(f"**Valor compra:** {moeda(prod.get('valor_compra'))}")
            d6.write(f"**Valor venda:** {moeda(prod.get('valor_venda'))}")
            d7.write(f"**Cód. barras:** {prod.get('codigo_barras') or '—'}")
            if prod.get("descricao"):
                st.caption(prod["descricao"])

            c_qtd, c_preco, c_tipo_desc, c_desc = st.columns(4)
            qtd = c_qtd.number_input("Quantidade *", min_value=1, value=1, step=1, key="prod_add_qtd")
            preco = c_preco.number_input(
                "Valor unitário (R$) *", min_value=0.0, value=float(prod.get("valor_compra") or 0),
                step=0.01, format="%.2f", key=f"prod_add_preco_{prod['id']}",
            )
            tipo_desc = c_tipo_desc.selectbox("Desconto em", ["Percentual (%)", "Valor (R$)"], key="prod_add_tipo_desc")
            desc = c_desc.number_input("Desconto", min_value=0.0, value=0.0, step=0.01, format="%.2f", key="prod_add_desc")

            bruto = qtd * preco
            if tipo_desc == "Percentual (%)":
                desc_pct, desc_val = desc, round(bruto * desc / 100, 2)
            else:
                desc_val, desc_pct = desc, round(desc / bruto * 100, 2) if bruto else 0.0

            st.markdown(
                f"<div style='text-align:right'>Desconto: {desc_pct:.2f}% = {moeda(desc_val)} · "
                f"<b>Total do item: {moeda(bruto - desc_val)}</b></div>",
                unsafe_allow_html=True,
            )

            if st.button("➕ Adicionar à compra", type="primary", use_container_width=True, key="btn_add_prod_compra"):
                if desc_val > bruto:
                    st.error("O desconto não pode ser maior que o valor do item.")
                else:
                    adicionar_item(int(prod["id"]), prod.get("produto", ""), int(qtd), float(preco), desc_pct, desc_val)
                    st.rerun()

    with tab_cad:
        with st.container(border=True):
            st.write("##### Cadastrar Novo Produto")

            marcas = MarcaService.listar_todas() or []
            unidades = UnidadeMedidaService.listar_todas() or []
            categorias = CategoriaService.listar_todas() or []
            op_marca = {m["marca"]: m["id"] for m in marcas}
            op_un = {f"{u['unidade_medida']} ({u['sigla']})": u["id"] for u in unidades}
            op_cat = {"Sem categoria": None, **{c["categoria"]: c["id"] for c in categorias}}

            c_nome, c_cod = st.columns([2, 1])
            p_nome = c_nome.text_input("Nome do Produto *", key="cad_p_nome")
            p_cod_barras = c_cod.text_input("Código de Barras", key="cad_p_cod_barras")

            c_marca, c_um, c_cat = st.columns(3)
            p_marca = c_marca.selectbox("Marca *", list(op_marca), key="cad_p_marca")
            p_um = c_um.selectbox("Unidade de Medida *", list(op_un), key="cad_p_um")
            p_cat = c_cat.selectbox("Categoria", list(op_cat), key="cad_p_cat")

            c_vvenda, c_info_custo = st.columns(2)
            p_val_venda = c_vvenda.number_input("Valor de Venda (R$) *", min_value=0.0, step=0.01, format="%.2f", key="cad_p_vvenda")
            c_info_custo.caption("O custo do produto é preenchido automaticamente ao lançar a compra.")

            p_desc = st.text_area("Descrição", key="cad_p_desc")

            if st.button("Salvar Produto", type="primary", use_container_width=True, key="btn_save_prod_modal"):
                if not p_nome or not p_marca or not p_um:
                    st.error("Informe Nome, Marca e Unidade de Medida.")
                else:
                    res = ProdutoService.criar({
                        "produto": p_nome,
                        "codigo_barras": p_cod_barras,
                        "valor_venda": p_val_venda,
                        "marca_id": op_marca[p_marca],
                        "unidade_medida_id": op_un[p_um],
                        "categoria_id": op_cat[p_cat],
                        "descricao": p_desc,
                    })
                    if res and res.data:
                        st.success(f"Produto cadastrado (Ref. {res.data[0]['id']}). Consulte-o na aba ao lado para adicionar.")
                    else:
                        st.error("Erro ao salvar produto no banco de dados.")


@st.dialog("Condição de Pagamento", width="large")
def condicao_pagamento_modal():
    if not condicoes_db:
        st.info("Nenhuma condição de pagamento ativa cadastrada.")
        return

    for cp in condicoes_db:
        parcelas = CondicaoPagamentoService.listar_parcelas(cp["id"])
        selecionada = st.session_state.condicao_compra_sel == cp["condicao_pagamento"]
        with st.container(border=True):
            c_info, c_btn = st.columns([4, 1])
            with c_info:
                st.write(f"**{cp['condicao_pagamento']}**" + ("  ✅" if selecionada else ""))
                st.caption(
                    " · ".join(
                        f"{p['numero_parcela']}ª: {p['dias']} dias – {float(p['percentual']):.2f}% – {p.get('forma_pagamento_nome') or ''}"
                        for p in parcelas
                    ) or "Sem parcelas cadastradas"
                )
            if c_btn.button("Selecionar", key=f"btn_sel_cond_{cp['id']}", use_container_width=True, disabled=not parcelas):
                st.session_state.condicao_compra_sel = cp["condicao_pagamento"]
                st.rerun()


# --- TELA PRINCIPAL ---

# Campos numéricos alinhados à direita
st.markdown(
    "<style>input[type='number'] { text-align: right; }</style>",
    unsafe_allow_html=True,
)

st.caption("Compras")
st.title("Compras")

tab_lista, tab_nova = st.tabs(["🔍 Compras cadastradas", "➕ Nova compra"])

# -----------------------------------------------------------------------------
# TAB 1: COMPRAS CADASTRADAS (LANÇADAS E CANCELADAS)
# -----------------------------------------------------------------------------
with tab_lista:
    c_busca, c_sit = st.columns([3, 1])
    busca = c_busca.text_input("Buscar", placeholder="Número da nota, fornecedor ou CNPJ/CPF...", key="busca_compras")
    filtro_sit = c_sit.selectbox("Situação", ["Todas", "Lançadas", "Canceladas"], key="filtro_sit_compras")
    situacao = {"Todas": None, "Lançadas": "LANCADA", "Canceladas": "CANCELADA"}[filtro_sit]

    compras = compra_service.listar_todas(busca=busca or None, situacao=situacao)

    if not compras:
        st.info("Nenhuma compra encontrada.")
    else:
        df_compras = pd.DataFrame([
            {
                "Modelo": c["modelo"],
                "Série": c["serie"],
                "Número": c["numero"],
                "Fornecedor": f"{c.get('fornecedor_nome', '')} ({c['fornecedor_cnpj_cpf']})",
                "Emissão": pd.to_datetime(c["data_emissao"]).date(),
                "Chegada": pd.to_datetime(c["data_chegada"]).date(),
                "Total": float(c.get("total_compra") or 0),
                "Situação": "🟢 Lançada" if c["situacao"] == "LANCADA" else "🔴 Cancelada",
            }
            for c in compras
        ])
        evento = st.dataframe(
            df_compras,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="grid_compras",
            column_config={
                "Emissão": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Chegada": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Total": st.column_config.NumberColumn(format="R$ %.2f"),
            },
        )

        if evento.selection.rows:
            sel = compras[evento.selection.rows[0]]
            chave = {k: sel[k] for k in ("modelo", "serie", "numero", "fornecedor_cnpj_cpf")}
            detalhe = compra_service.obter(chave)

            if detalhe:
                st.markdown("---")
                st.subheader(f"Nota {detalhe['modelo']}/{detalhe['serie']}/{detalhe['numero']} – {detalhe['fornecedor_nome']}")
                if detalhe["situacao"] == "CANCELADA":
                    st.error(
                        f"Compra cancelada em {pd.to_datetime(detalhe['data_cancelamento']).strftime('%d/%m/%Y %H:%M')}"
                        f" – Motivo: {detalhe.get('motivo_cancelamento') or '—'}"
                    )

                st.write("**Produtos**")
                st.dataframe(
                    pd.DataFrame(detalhe["itens"])[
                        ["produto_id", "produto", "quantidade", "preco_unitario", "custo_rateio", "custo_unitario",
                         "desconto_percentual", "desconto_valor", "total_item"]
                    ] if detalhe["itens"] else pd.DataFrame(),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "produto_id": "Ref.",
                        "produto": "Produto",
                        "quantidade": "Qtd",
                        "preco_unitario": st.column_config.NumberColumn("Valor unit.", format="R$ %.2f"),
                        "custo_rateio": st.column_config.NumberColumn("Custo (rateio)", format="R$ %.2f"),
                        "custo_unitario": st.column_config.NumberColumn("Custo unit.", format="R$ %.4f"),
                        "desconto_percentual": st.column_config.NumberColumn("Desc. %", format="%.2f%%"),
                        "desconto_valor": st.column_config.NumberColumn("Desc. R$", format="R$ %.2f"),
                        "total_item": st.column_config.NumberColumn("Total", format="R$ %.2f"),
                    },
                )

                c_fech, c_parc = st.columns(2)
                with c_fech:
                    st.write("**Fechamento**")
                    st.markdown(
                        "<div style='text-align:right'>"
                        f"Produtos: {moeda(detalhe['total_produtos'])}<br>"
                        f"Frete: {moeda(detalhe['frete'])} · Seguro: {moeda(detalhe['seguro'])} · "
                        f"Outras: {moeda(detalhe['outras_despesas'])}<br>"
                        f"<b>Total da compra: {moeda(detalhe['total_compra'])}</b><br>"
                        f"Transportadora: {detalhe.get('transportadora') or 'Sem transportadora'}"
                        "</div>",
                        unsafe_allow_html=True,
                    )
                with c_parc:
                    st.write(f"**Parcelas – {detalhe.get('condicao_pagamento') or ''}**")
                    st.dataframe(
                        pd.DataFrame(detalhe["parcelas"])[["parcela", "vencimento", "valor", "forma_pagamento"]]
                        if detalhe["parcelas"] else pd.DataFrame(),
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "parcela": "Parcela",
                            "vencimento": st.column_config.DateColumn("Vencimento", format="DD/MM/YYYY"),
                            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f"),
                            "forma_pagamento": "Forma",
                        },
                    )

                if detalhe["situacao"] == "LANCADA":
                    with st.container(border=True):
                        st.write("**Cancelar compra** (o estoque dos produtos será estornado)")
                        motivo = st.text_input("Motivo do cancelamento *", key="motivo_cancelamento")
                        if st.button("🔴 Cancelar compra", type="primary", key="btn_cancelar_compra"):
                            if not motivo.strip():
                                st.error("Informe o motivo do cancelamento.")
                            else:
                                ok, msg = compra_service.cancelar(chave, motivo.strip())
                                if ok:
                                    st.toast(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

# -----------------------------------------------------------------------------
# TAB 2: NOVA COMPRA (ETAPAS SEQUENCIAIS)
# -----------------------------------------------------------------------------
# Botões que abrem popups: os modais são chamados no fim do script
acoes = {}


def renderizar_nova_compra():
    hoje = datetime.date.today()
    v = st.session_state.versao_form_compra
    forn_sel = st.session_state.fornecedor_compra_selecionado
    transp_sel = st.session_state.transportadora_compra_selecionada
    nota_ok = st.session_state.nota_confirmada

    # Mantém frete/seguro/outras mesmo nas execuções em que a etapa 3 não é exibida
    for campo in ("inp_frete", "inp_seguro", "inp_outras"):
        if f"{campo}_{v}" in st.session_state:
            st.session_state[f"{campo}_{v}"] = st.session_state[f"{campo}_{v}"]

    # ---------------- 1. DADOS DA NOTA ----------------
    st.subheader("1. Dados da nota")

    col_mod, col_ser, col_num = st.columns(3)
    modelo = col_mod.text_input("Modelo *", value="55", key=f"nota_modelo_{v}", disabled=nota_ok)
    serie = col_ser.text_input("Série *", value="1", key=f"nota_serie_{v}", disabled=nota_ok)
    numero = col_num.text_input("Número *", placeholder="Ex: 000123", key=f"nota_numero_{v}", disabled=nota_ok)

    col_forn, col_btn_forn = st.columns([4, 1])
    with col_forn:
        val_forn = (
            f"{forn_sel['id']} – {forn_sel['nome']} – {forn_sel.get('cnpj_cpf', '')}" if forn_sel else ""
        )
        st.text_input("Fornecedor (ID – Razão Social – CNPJ/CPF) *", value=val_forn,
                      placeholder="Selecione um fornecedor...", disabled=True)
    with col_btn_forn:
        st.write("**Fornecedor**")
        acoes["forn"] = st.button("🏢 Buscar / Criar", use_container_width=True, disabled=nota_ok)

    col_dt_emissao, col_dt_chegada = st.columns(2)
    data_emissao = col_dt_emissao.date_input(
        "Data de emissão *", value=hoje, max_value=hoje, format="DD/MM/YYYY",
        key=f"nota_emissao_{v}", disabled=nota_ok,
    )
    data_chegada = col_dt_chegada.date_input(
        "Data de chegada *", value=hoje, min_value=data_emissao, max_value=hoje, format="DD/MM/YYYY",
        key=f"nota_chegada_{v}", disabled=nota_ok,
    )

    if not nota_ok:
        if st.button("✔️ Confirmar dados da nota", type="primary"):
            if not (modelo.strip() and serie.strip() and numero.strip()):
                st.error("Preencha Modelo, Série e Número.")
            elif not forn_sel:
                st.error("Selecione um Fornecedor através do botão '🏢 Buscar / Criar'.")
            elif data_emissao > hoje:
                st.error("A data de emissão não pode ser posterior a hoje.")
            elif data_chegada < data_emissao or data_chegada > hoje:
                st.error("A data de chegada deve estar entre a data de emissão e hoje.")
            elif compra_service.existe(modelo.strip(), serie.strip(), numero.strip(), forn_sel["cnpj_cpf"]):
                st.error("Já existe uma compra com este Modelo/Série/Número para este fornecedor.")
            else:
                st.session_state.nota_confirmada = True
                # Condição de pagamento do fornecedor vem pré-selecionada
                if forn_sel.get("condicao_pagamento") in condicoes_por_nome:
                    st.session_state.condicao_compra_sel = forn_sel["condicao_pagamento"]
                st.rerun()
        st.info("Confirme os dados da nota para liberar os produtos.")
        return
    elif st.button("✏️ Alterar dados da nota"):
        st.session_state.nota_confirmada = False
        st.rerun()

    st.markdown("---")

    # ---------------- 2. PRODUTOS ----------------
    st.subheader("2. Produtos")

    # Despesas lidas do estado dos campos da etapa 3 (renderizados mais abaixo)
    frete = float(st.session_state.get(f"inp_frete_{v}", 0.0) or 0.0)
    seguro = float(st.session_state.get(f"inp_seguro_{v}", 0.0) or 0.0)
    outras_despesas = float(st.session_state.get(f"inp_outras_{v}", 0.0) or 0.0)
    custos_adicionais = round(frete + seguro + outras_despesas, 2)

    acoes["prod"] = st.button("📦 Consultar / Adicionar Produto")

    itens = calcular_itens(st.session_state.itens_compra, custos_adicionais)

    if not itens:
        st.info("Nenhum produto adicionado.")
    else:
        colunas = ["produto_id", "produto", "quantidade", "preco_unitario", "custo_rateio", "custo_unitario",
                   "desconto_percentual", "desconto_valor", "total_item"]
        df_itens = pd.DataFrame(itens)[colunas]

        edited = st.data_editor(
            df_itens,
            column_config={
                "produto_id": st.column_config.NumberColumn("Ref.", disabled=True),
                "produto": st.column_config.TextColumn("Produto", disabled=True),
                "quantidade": st.column_config.NumberColumn("Qtd", min_value=1, step=1),
                "preco_unitario": st.column_config.NumberColumn("Valor unit. (R$)", min_value=0.0, format="R$ %.2f"),
                "custo_rateio": st.column_config.NumberColumn("Custo (R$)", disabled=True, format="R$ %.2f",
                                                              help="Rateio de frete + seguro + outras despesas"),
                "custo_unitario": st.column_config.NumberColumn("Custo unit. (R$)", disabled=True, format="R$ %.4f",
                                                                help="(Total do item + custo) / quantidade"),
                "desconto_percentual": st.column_config.NumberColumn("Desc. %", min_value=0.0, max_value=100.0, format="%.2f"),
                "desconto_valor": st.column_config.NumberColumn("Desc. R$", min_value=0.0, format="R$ %.2f"),
                "total_item": st.column_config.NumberColumn("Total (R$)", disabled=True, format="R$ %.2f"),
            },
            num_rows="fixed",
            hide_index=True,
            use_container_width=True,
            key=f"editor_itens_{st.session_state.versao_editor_itens}",
        )

        # Sincroniza desconto % <-> R$ conforme o campo que foi alterado
        novos, mudou = [], False
        for anterior, linha in zip(st.session_state.itens_compra, edited.to_dict("records")):
            qtd = int(linha["quantidade"] or 1)
            preco = float(linha["preco_unitario"] or 0)
            pct = float(linha["desconto_percentual"] or 0)
            val = float(linha["desconto_valor"] or 0)
            bruto = qtd * preco
            if pct != anterior["desconto_percentual"]:
                val = round(bruto * pct / 100, 2)
            elif val != anterior["desconto_valor"]:
                pct = round(val / bruto * 100, 2) if bruto else 0.0
            elif qtd != anterior["quantidade"] or preco != anterior["preco_unitario"]:
                val = round(bruto * pct / 100, 2)
            val = min(val, round(bruto, 2))
            novo = {**anterior, "quantidade": qtd, "preco_unitario": preco,
                    "desconto_percentual": pct, "desconto_valor": val}
            mudou = mudou or novo != anterior
            novos.append(novo)
        if mudou:
            st.session_state.itens_compra = novos
            st.session_state.versao_editor_itens += 1
            st.rerun()

        c_rem, c_btn_rem = st.columns([4, 1])
        item_remover = c_rem.selectbox(
            "Remover produto", options=range(len(itens)),
            format_func=lambda i: f"{itens[i]['produto_id']} – {itens[i]['produto']}",
            key="sel_item_remover", label_visibility="collapsed",
        )
        if c_btn_rem.button("🗑️ Remover", use_container_width=True):
            st.session_state.itens_compra.pop(item_remover)
            st.session_state.versao_editor_itens += 1
            st.rerun()

    total_bruto = sum(i["quantidade"] * i["preco_unitario"] for i in itens)
    desconto_total = round(sum(i["desconto_valor"] for i in itens), 2)
    total_produtos = round(sum(i["total_item"] for i in itens), 2)
    total_compra = round(total_produtos + custos_adicionais, 2)

    st.markdown(
        f"<div style='text-align:right'><b>Total dos produtos: {moeda(total_produtos)}</b></div>",
        unsafe_allow_html=True,
    )

    if not itens:
        return

    st.markdown("---")

    # ---------------- 3. FRETE E TRANSPORTADORA ----------------
    st.subheader("3. Frete e Transportadora")

    col_transp, col_btn_transp = st.columns([4, 1])
    with col_transp:
        st.text_input("Transportadora", value=transp_sel.get("nome", "") if transp_sel else "Sem transportadora",
                      disabled=True)
    with col_btn_transp:
        st.write("**Transportadora**")
        acoes["transp"] = st.button("🚚 Buscar / Criar", use_container_width=True)

    c_frete, c_seguro, c_outras = st.columns(3)
    c_frete.number_input("Frete (R$)", min_value=0.0, step=10.0, format="%.2f", key=f"inp_frete_{v}")
    c_seguro.number_input("Seguro (R$)", min_value=0.0, step=10.0, format="%.2f", key=f"inp_seguro_{v}")
    c_outras.number_input("Outras despesas (R$)", min_value=0.0, step=10.0, format="%.2f", key=f"inp_outras_{v}")

    st.markdown("---")

    # ---------------- 4. FECHAMENTO ----------------
    st.subheader("4. Fechamento")
    st.markdown(
        "<table style='width:100%;text-align:right'>"
        "<tr><th style='text-align:right'>Total bruto</th><th style='text-align:right'>Descontos</th>"
        "<th style='text-align:right'>Total produtos</th><th style='text-align:right'>Frete</th>"
        "<th style='text-align:right'>Seguro</th><th style='text-align:right'>Outras despesas</th>"
        "<th style='text-align:right'>Total da compra</th></tr>"
        f"<tr><td>{moeda(total_bruto)}</td><td>- {moeda(desconto_total)}</td><td>{moeda(total_produtos)}</td>"
        f"<td>{moeda(frete)}</td><td>{moeda(seguro)}</td><td>{moeda(outras_despesas)}</td>"
        f"<td><b>{moeda(total_compra)}</b></td></tr></table>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ---------------- 5. CONDIÇÃO DE PAGAMENTO ----------------
    st.subheader("5. Condição de pagamento")

    cond_nome = st.session_state.condicao_compra_sel
    col_cond, col_btn_cond = st.columns([4, 1])
    with col_cond:
        st.text_input("Condição de pagamento *", value=cond_nome or "", placeholder="Selecione a condição...",
                      disabled=True)
    with col_btn_cond:
        st.write("**Condição**")
        acoes["cond"] = st.button("📋 Selecionar", use_container_width=True)

    assinatura = (cond_nome, data_emissao, total_compra)

    def gerar():
        parcelas_cond = CondicaoPagamentoService.listar_parcelas(condicoes_por_nome[cond_nome]["id"])
        st.session_state.parcelas_compra = gerar_parcelas(parcelas_cond, data_emissao, total_compra)
        st.session_state.assinatura_parcelas = assinatura

    if not st.session_state.parcelas_compra:
        if st.button("Gerar parcelas", type="primary", disabled=not cond_nome):
            if total_compra <= 0:
                st.error("O total da compra deve ser maior que zero.")
            else:
                gerar()
                st.rerun()
    else:
        # Mantém as parcelas coerentes com qualquer alteração feita antes de lançar
        if st.session_state.assinatura_parcelas != assinatura:
            if cond_nome and total_compra > 0:
                gerar()
                st.info("Parcelas recalculadas conforme as alterações da compra.")
            else:
                st.session_state.parcelas_compra = []
                st.session_state.assinatura_parcelas = None
                st.rerun()
        parcelas = st.session_state.parcelas_compra
        df_parc = pd.DataFrame(parcelas)
        df_parc.insert(0, "Parcela", [f"{i + 1}/{len(parcelas)}" for i in range(len(parcelas))])
        st.dataframe(
            df_parc[["Parcela", "Vencimento", "Valor", "Forma"]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "Vencimento": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            },
        )

    st.markdown("---")

    # ---------------- BOTÕES FINAIS ----------------
    col_b1, col_lancar, col_cancelar = st.columns([4, 1, 1])
    btn_lancar = col_lancar.button("Lançar compra", type="primary", use_container_width=True, disabled=not st.session_state.parcelas_compra)
    btn_cancelar = col_cancelar.button("Cancelar", use_container_width=True)

    if btn_cancelar:
        limpar_compra()
        st.rerun()

    if btn_lancar:
        cond = condicoes_por_nome.get(cond_nome, {})
        parcelas = st.session_state.parcelas_compra
        dados_compra = {
            "modelo": modelo.strip(),
            "serie": serie.strip(),
            "numero": numero.strip(),
            "fornecedor_cnpj_cpf": forn_sel["cnpj_cpf"],
            "fornecedor_id": forn_sel.get("id"),
            "fornecedor_nome": forn_sel["nome"],
            "data_emissao": str(data_emissao),
            "data_chegada": str(data_chegada),
            "transportadora_id": transp_sel.get("id") if transp_sel else None,
            "transportadora": transp_sel.get("nome") if transp_sel else None,
            "frete": frete,
            "seguro": seguro,
            "outras_despesas": outras_despesas,
            "total_produtos": total_produtos,
            "desconto_total": desconto_total,
            "custos_adicionais": custos_adicionais,
            "total_compra": total_compra,
            "condicao_pagamento_id": cond.get("id"),
            "condicao_pagamento": cond_nome,
            "forma_pagamento": parcelas[0].get("Forma") if parcelas else None,
        }
        itens_payload = [
            {k: i[k] for k in ("produto_id", "produto", "quantidade", "preco_unitario", "desconto_percentual",
                               "desconto_valor", "total_item", "custo_rateio", "custo_unitario")}
            for i in itens
        ]
        parcelas_payload = [
            {
                "numero_parcela": n + 1,
                "parcela": f"{n + 1}/{len(parcelas)}",
                "vencimento": str(p["Vencimento"]),
                "valor": float(p["Valor"]),
                "forma_pagamento": p.get("Forma") or None,
            }
            for n, p in enumerate(parcelas)
        ]

        ok, res = compra_service.lancar(dados_compra, itens_payload, parcelas_payload)
        if ok:
            st.toast("Compra lançada com sucesso! Estoque atualizado.")
            limpar_compra()
            st.rerun()
        else:
            st.error(f"Erro ao lançar compra: {res}")


with tab_nova:
    renderizar_nova_compra()

# --- AÇÕES PARA ABRIR OS MODAIS ---
if acoes.get("forn"):
    gerenciar_fornecedores_modal()

if acoes.get("transp"):
    gerenciar_transportadoras_modal()

if acoes.get("prod"):
    consultar_produto_modal()

if acoes.get("cond"):
    condicao_pagamento_modal()
