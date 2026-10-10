import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from supabase import Client, create_client

from services.transportadora_service import TransportadoraService
from services.veiculo_service import VeiculoService
from utils.inputs import aplicar_padrao_inputs
from utils.veiculos_ui import TIPOS_VEICULO

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
service = VeiculoService(supabase)
transp_service = TransportadoraService(supabase)

st.set_page_config(page_title="Veículos", layout="wide")
aplicar_padrao_inputs()

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "veiculo_para_editar" not in st.session_state:
    st.session_state.veiculo_para_editar = None

if "veiculo_msg" not in st.session_state:
    st.session_state.veiculo_msg = None

# Incrementado para limpar os campos do formulário após salvar/cancelar
if "versao_form_veiculo" not in st.session_state:
    st.session_state.versao_form_veiculo = 0


def limpar_formulario_veiculo():
    st.session_state.veiculo_para_editar = None
    st.session_state.versao_form_veiculo += 1


# --- TELA PRINCIPAL: FORMULÁRIO DE CADASTRO / EDIÇÃO DE VEÍCULO ---

veic_edit = st.session_state.veiculo_para_editar
modo_edicao = veic_edit is not None
ve = veic_edit or {}
v = st.session_state.versao_form_veiculo

titulo = "✏️ Editar Veículo" if modo_edicao else "Novo Veículo"
st.caption(f"Veículos / {titulo}")
st.title(titulo)

if st.session_state.veiculo_msg:
    st.success(st.session_state.veiculo_msg)
    st.session_state.veiculo_msg = None

transportadoras_ativas = transp_service.listar_todos(apenas_ativos=True) or []
opcoes_transp = {"Sem transportadora": None}
opcoes_transp.update({t["razao_social"]: t["id"] for t in transportadoras_ativas if t.get("razao_social")})
# Mantém a transportadora atual na lista mesmo que esteja desativada
transp_atual = ve.get("transportadora") if isinstance(ve.get("transportadora"), dict) else None
if transp_atual and ve.get("transportadora_id") not in opcoes_transp.values():
    opcoes_transp[transp_atual.get("razao_social", "")] = ve["transportadora_id"]
nomes_transp = list(opcoes_transp)
idx_transp = next(
    (i for i, nome in enumerate(nomes_transp) if opcoes_transp[nome] == ve.get("transportadora_id")),
    0,
)

with st.form(f"form_veiculo_{v}", clear_on_submit=False):

    col_placa, col_modelo, col_marca, col_status = st.columns([1, 2, 2, 1])
    placa = col_placa.text_input("Placa *", value=ve.get("placa") or "", max_chars=10, placeholder="AAA0A00")
    modelo = col_modelo.text_input("Modelo *", value=ve.get("modelo") or "", placeholder="Ex: FH 540")
    marca = col_marca.text_input("Marca", value=ve.get("marca") or "", placeholder="Ex: VOLVO")
    with col_status:
        st.write("Status")
        ativo = st.toggle("Ativo", value=bool(ve.get("ativo", True)))

    col_tipo, col_ano, col_cap = st.columns(3)
    tipo_padrao = ve.get("tipo")
    tipo = col_tipo.selectbox(
        "Tipo",
        TIPOS_VEICULO,
        index=TIPOS_VEICULO.index(tipo_padrao) if tipo_padrao in TIPOS_VEICULO else 0,
    )
    ano = col_ano.number_input("Ano", min_value=0, max_value=2100, value=int(ve.get("ano") or 0), step=1)
    capacidade = col_cap.number_input(
        "Capacidade (kg)", min_value=0.0, value=float(ve.get("capacidade_kg") or 0.0), step=100.0
    )

    col_renavam, col_rntrc, col_transp = st.columns(3)
    renavam = col_renavam.text_input("RENAVAM", value=ve.get("renavam") or "")
    rntrc = col_rntrc.text_input("RNTRC", value=ve.get("rntrc") or "")
    transportadora = col_transp.selectbox("Transportadora", nomes_transp, index=idx_transp)

    observacoes = st.text_area(
        "Observações", value=ve.get("observacoes") or "", placeholder="Observações adicionais", height=100
    )

    st.markdown("---")

    col_b1, col_salvar, col_cancelar = st.columns([5, 1.5, 1])
    with col_salvar:
        btn_salvar = st.form_submit_button(
            "Salvar Alterações" if modo_edicao else "Salvar",
            type="primary",
            use_container_width=True,
        )
    with col_cancelar:
        btn_cancelar = st.form_submit_button("Cancelar", use_container_width=True)

# Lógica de Gravação no Supabase
if btn_salvar:
    placa_limpa = placa.strip().replace("-", "").replace(" ", "")
    if not placa_limpa or not modelo.strip():
        st.error("Por favor, preencha todos os campos obrigatórios marcados com (*).")
    else:
        dados = {
            "placa": placa_limpa,
            "modelo": modelo.strip(),
            "marca": marca.strip() or None,
            "tipo": tipo,
            "ano": int(ano) or None,
            "capacidade_kg": capacidade,
            "renavam": renavam.strip() or None,
            "rntrc": rntrc.strip() or None,
            "transportadora_id": opcoes_transp[transportadora],
            "ativo": ativo,
            "observacoes": observacoes,
        }

        if modo_edicao:
            sucesso, resultado = service.editar(veic_edit["id"], dados)
            msg = f"Veículo {placa_limpa} atualizado com sucesso!"
        else:
            sucesso, resultado = service.criar(dados)
            msg = "Veículo cadastrado com sucesso!"

        if sucesso:
            limpar_formulario_veiculo()
            st.session_state.veiculo_msg = msg
            st.rerun()
        else:
            st.error(resultado)

if btn_cancelar:
    limpar_formulario_veiculo()
    st.rerun()

# --- LISTAGEM DE VEÍCULOS CADASTRADOS ---
st.write("")
st.subheader("📊 Veículos Cadastrados")

col_busca, col_desat = st.columns([3, 1])
busca_veic = col_busca.text_input("Buscar", placeholder="Placa, modelo ou marca...", key="busca_veiculos")
col_desat.write("")
exibir_desativados = col_desat.checkbox("👁️ Exibir desativados", value=False, key="chk_veic_desat")

veiculos = service.listar_todos(busca=busca_veic.strip() or None, apenas_ativos=not exibir_desativados)

if veiculos:
    df_veic = pd.DataFrame([
        {
            "ID": vc["id"],
            "Placa": vc.get("placa") or "",
            "Modelo": vc.get("modelo") or "",
            "Marca": vc.get("marca") or "",
            "Tipo": vc.get("tipo") or "",
            "Ano": vc.get("ano") or "",
            "Transportadora": (vc.get("transportadora") or {}).get("razao_social", ""),
            "Status": "🟢 Ativo" if vc.get("ativo", True) else "🔴 Desativado",
        }
        for vc in veiculos
    ])

    evento_grid = st.dataframe(
        df_veic,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun",
        key="grid_veiculos",
    )

    if evento_grid.selection.rows:
        veic_escolhido = veiculos[evento_grid.selection.rows[0]]

        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(
            f"Item Selecionado: ID **{veic_escolhido['id']}** - **{veic_escolhido.get('placa', '')}**"
        )

        if c_edit.button("✏️ Editar Selecionado", use_container_width=True):
            st.session_state.veiculo_para_editar = veic_escolhido
            st.session_state.versao_form_veiculo += 1
            st.rerun()

        esta_ativo = bool(veic_escolhido.get("ativo", True))
        texto_botao = "❌ Desativar" if esta_ativo else "🔄 Reativar"
        cor_botao = "primary" if esta_ativo else "secondary"

        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            sucesso, resultado = service.alternar_status(veic_escolhido["id"], not esta_ativo)
            if sucesso:
                st.session_state.veiculo_msg = "Status alterado com sucesso!"
                st.rerun()
            else:
                st.error(resultado)
else:
    st.info("Nenhum veículo localizado com os filtros aplicados.")
