import streamlit as st
from services.cliente_service import ClienteService
from services.cidade_service import CidadeService
from services.pais_service import PaisService
from utils.utils import validar_cpf
from datetime import date

st.set_page_config(page_title="Gestão de Clientes", layout="wide")
st.title("👤 Cadastro de Clientes")

# Carregar dados para os selects
cidades = CidadeService.listar_todos()
cidades_dict = {f"{c['nome']} - {c['estado']['uf']}": c['id'] for c in cidades}

paises = PaisService.listar_todos()
paises_dict = {p['nome']: p['id'] for p in paises}

with st.expander("Novo Cliente", expanded=True):
    # 1. PRIMEIRO abrimos o Form
    with st.form("form_cliente", clear_on_submit=True):
        
        col1, col2 = st.columns(2)
        nome = col1.text_input("Cliente*", placeholder="Ex: Maria Silva")
        apelido = col2.text_input("Apelido")
        
        col3, col4, col5 = st.columns([0.4, 0.3, 0.1])
        cpf = col3.text_input("CPF (Somente números)*")
        nascimento = col4.date_input("Data de Nascimento", min_value=date(1920, 1, 1), max_value=date.today())
        sexo = col5.selectbox("Sexo", options=["M", "F"], index=1)


        col_cep, col_rua, col_num = st.columns([0.2, 0.6, 0.2])
        cep = col_cep.text_input("CEP")
        endereco = col_rua.text_input("Rua/Logradouro")
        numero = col_num.text_input("Nº")
        
        col_bairro, col_cidade = st.columns(2)
        bairro = col_bairro.text_input("Bairro")
        cidade_label = col_cidade.selectbox("Cidade/UF", options=list(cidades_dict.keys()))
        complemento = st.text_input("Complemento")

        nacionalidade_label = st.selectbox("Nacionalidade", options=list(paises_dict.keys()), index=0)
        col6, col7 = st.columns(2)
        email = col6.text_input("E-mail")
        telefone_cliente = col7.text_input("Telefone", key="input_telefone")
        observacao = st.text_area("Preferências ou Observações")

        # O botão DEVE estar dentro do 'with st.form'
        submit = st.form_submit_button("Finalizar Cadastro")

        if submit:
            if not nome or not cpf:
                st.error("Campos com * são obrigatórios.")
            elif not validar_cpf(cpf):
                st.error("CPF inválido! Verifique os números.")
            else:
                novo_cliente = {
                    "cliente": nome,
                    "apelido": apelido,
                    "cpf": cpf,
                    "email": email,
                    "telefone": telefone_cliente, 
                    "data_nascimento": str(nascimento),
                    "sexo": sexo,
                    "cep": cep,
                    "endereco": endereco,
                    "numero": numero,
                    "bairro": bairro,
                    "complemento": complemento,
                    "cidade_id": cidades_dict[cidade_label],
                    "nacionalidade_id": paises_dict[nacionalidade_label],
                    "observacao": observacao,
                    "ativo": True
                }
                
                try:
                    ClienteService.criar(novo_cliente)
                    st.success(f"Cliente {nome} cadastrado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no Supabase: {e}")

# --- LISTAGEM ---
clientes = ClienteService.listar_todos()
if clientes:
    st.subheader("Clientes Cadastrados")
    # Tabela simples para visualização
    data_table = []
    for c in clientes:
        data_table.append({
            "Nome": c['cliente'],
            "CPF": c['cpf'],
            "Telefone": c['telefone'],
            "Cidade": f"{c['cidade']['nome']}/{c['cidade']['estado']['uf']}" if c['cidade'] else "N/A"
        })
    st.table(data_table)
else:
    st.info("Nenhum cliente cadastrado.")