import os
from dotenv import load_dotenv
import streamlit as st
from supabase import Client, create_client
from services.fornecedor_service import FornecedorService

# Carrega as variáveis do ficheiro .env
load_dotenv()


@st.cache_resource
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        st.error(
            "As variáveis SUPABASE_URL e SUPABASE_KEY não foram encontradas no"
            " ficheiro .env."
        )
        st.stop()

    return create_client(url, key)


# Inicializa o cliente do Supabase e o Serviço
supabase = init_supabase()
service = FornecedorService(supabase)

st.set_page_config(page_title="Novo Fornecedor", layout="wide")

# Cabeçalho
st.caption("Fornecedores / Novo Fornecedor")
st.title("Novo Fornecedor")

# Gestão de estado para múltiplos e-mails e telefones
if "emails" not in st.session_state:
    st.session_state.emails = []
if "telefones" not in st.session_state:
    st.session_state.telefones = []

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

    # País, Estado e Cidade
    col_pais, col_uf, col_cidade = st.columns([1, 1, 1])
    with col_pais:
        pais = st.selectbox("País *", ["Brasil", "Outro"], index=0)
    with col_uf:
        estado = st.selectbox(
            "Estado *",
            [
                "",
                "AC",
                "AL",
                "AP",
                "AM",
                "BA",
                "CE",
                "DF",
                "ES",
                "GO",
                "MA",
                "MT",
                "MS",
                "MG",
                "PA",
                "PB",
                "PR",
                "PE",
                "PI",
                "RJ",
                "RN",
                "RS",
                "RO",
                "RR",
                "SC",
                "SP",
                "SE",
                "TO",
            ],
        )
    with col_cidade:
        cidade = st.text_input(
            "Cidade *", placeholder="Digite ou selecione a cidade"
        )

    # Complemento e Bairro
    col_comp, col_bairro = st.columns([1, 1])
    with col_comp:
        complemento = st.text_input(
            "Complemento", placeholder="Apto, bloco, sala..."
        )
    with col_bairro:
        bairro = st.text_input("Bairro", placeholder="Bairro")

    # Condição de Pagamento, Limite de Crédito e Transportadora
    col_cond, col_limite, col_transp = st.columns([1, 1, 1])
    with col_cond:
        condicao_pagamento = st.selectbox(
            "Condição de Pagamento *",
            [
                "A vista",
                "30 dias",
                "30/60 dias",
                "30/60/90 dias",
                "Personalizado",
            ],
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

    # Botões de Ação
    col_b1, col_b2, col_salvar, col_cancelar = st.columns([5, 1, 1, 1])
    with col_salvar:
        btn_salvar = st.form_submit_button(
            "Salvar", type="primary", use_container_width=True
        )
    with col_cancelar:
        btn_cancelar = st.form_submit_button(
            "Cancelar", use_container_width=True
        )

# Submissão do Formulário
if btn_salvar:
    # Captura valores pendentes nos campos de e-mail/telefone
    if novo_email and novo_email not in st.session_state.emails:
        st.session_state.emails.append(novo_email)
    if novo_tel and novo_tel not in st.session_state.telefones:
        st.session_state.telefones.append(novo_tel)

    # Validação de campos obrigatórios
    if not razao_social or not cnpj_cpf or not estado or not cidade:
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
            "complemento": complemento,
            "bairro": bairro,
            "condicao_pagamento": condicao_pagamento,
            "limite_credito": limite_credito,
            "transportadora": transportadora,
            "emails": st.session_state.emails,
            "telefones": st.session_state.telefones,
            "observacoes": observacoes,
        }

        # Chamada ao FornecedorService
        sucesso, resultado = service.criar(dados)

        if sucesso:
            st.success("Fornecedor cadastrado com sucesso!")
            st.session_state.emails = []
            st.session_state.telefones = []
        else:
            st.error(f"Erro ao salvar fornecedor: {resultado}")

if btn_cancelar:
    st.info("Cadastro cancelado.")
    st.session_state.emails = []
    st.session_state.telefones = []