import pandas as pd
import streamlit as st
from services.condicaopag_service import CondicaoPagamentoService

st.set_page_config(
    page_title="Condições de Pagamento", layout="wide", page_icon="💳"
)

# --- ESTADOS DA SESSÃO ---
if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = False

if "condicao_em_edicao" not in st.session_state:
    st.session_state.condicao_em_edicao = None


def limpar_formulario():
    st.session_state.modo_edicao = False
    st.session_state.condicao_em_edicao = None


st.caption("Cadastros / Condições de Pagamento")
st.title("💳 Gestão de Condições de Pagamento")

# --- ABAS DE NAVEGAÇÃO ---
tab_consulta, tab_cadastro = st.tabs(
    ["🔍 Listagem e Consulta", "➕ Nova / Editar Condição"]
)

# -----------------------------------------------------------------------------
# TAB 1: LISTAGEM E CONSULTA
# -----------------------------------------------------------------------------
with tab_consulta:
    col_busca, col_filtro = st.columns([3, 1])

    with col_busca:
        termo_busca = st.text_input(
            "Buscar Condição", placeholder="Digite o nome da condição..."
        )

    with col_filtro:
        exibir_desativados = st.checkbox(
            "Exibir inativos", value=False, key="chk_exibir_inativos"
        )

    # Carrega os dados do banco
    dados = CondicaoPagamentoService.listar_todas(
        apenas_ativos=not exibir_desativados
    )

    if dados:
        df = pd.DataFrame(dados)

        # Filtro local de busca por texto
        if termo_busca:
            df = df[
                df["condicao_pagamento"]
                .str.lower()
                .str.contains(termo_busca.lower(), na=False)
            ]

        # Formatação das colunas para exibição na tabela
        df_exibicao = pd.DataFrame({
            "ID": df["id"],
            "Condição de Pagamento": df["condicao_pagamento"],
            "Parcelas": df["numero_parcelas"],
            "Dias/Prazo": df["dias"],
            "Juros (%)": df["percentual_juros"].apply(
                lambda x: f"{float(x or 0):.2f}%"
            ),
            "Multa (%)": df["percentual_multa"].apply(
                lambda x: f"{float(x or 0):.2f}%"
            ),
            "Desconto (%)": df["percentual_desconto"].apply(
                lambda x: f"{float(x or 0):.2f}%"
            ),
            "Status": df["ativo"].apply(
                lambda a: "🟢 Ativo" if a else "🔴 Inativo"
            ),
        })

        st.subheader("Registros Cadastrados")
        evento = st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="grid_condicoes",
        )

        # Ações sobre o registro selecionado
        if evento.selection.rows:
            idx = evento.selection.rows[0]
            registro_selecionado = df.iloc[idx].to_dict()

            st.markdown("---")
            col_info, col_btn_edit, col_btn_status = st.columns([4, 1, 1])

            with col_info:
                st.write(
                    f"**Selecionado:** {registro_selecionado['condicao_pagamento']} | "
                    f"**Parcelas:** {registro_selecionado['numero_parcelas']}x | "
                    f"**Dias:** {registro_selecionado['dias']} dias"
                )

            with col_btn_edit:
                if st.button(
                    "✏️ Editar", use_container_width=True, type="secondary"
                ):
                    st.session_state.modo_edicao = True
                    st.session_state.condicao_em_edicao = registro_selecionado
                    st.rerun()

            with col_btn_status:
                status_atual = registro_selecionado["ativo"]
                label_btn = "🔴 Desativar" if status_atual else "🟢 Ativar"
                if st.button(label_btn, use_container_width=True):
                    CondicaoPagamentoService.alternar_status(
                        registro_selecionado["id"]
                    )
                    st.toast("Status alterado com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhuma condição de pagamento encontrada.")

# -----------------------------------------------------------------------------
# TAB 2: FORMULÁRIO DE CADASTRO / EDIÇÃO
# -----------------------------------------------------------------------------
with tab_cadastro:
    em_edicao = st.session_state.modo_edicao
    dados_edicao = st.session_state.condicao_em_edicao or {}

    if em_edicao:
        st.subheader(
            f"✏️ Editando: {dados_edicao.get('condicao_pagamento', '')}"
        )
    else:
        st.subheader("➕ Nova Condição de Pagamento")

    with st.form("form_condicao_pagamento", clear_on_submit=not em_edicao):
        nome_condicao = st.text_input(
            "Descrição / Nome da Condição *",
            value=dados_edicao.get("condicao_pagamento", ""),
            placeholder="Ex: A VISTA, 30 DIAS, 30/60/90 DIAS",
        )

        col_parc, col_dias = st.columns(2)
        with col_parc:
            num_parcelas = st.number_input(
                "Número de Parcelas *",
                min_value=1,
                value=int(dados_edicao.get("numero_parcelas", 1)),
                step=1,
            )
        with col_dias:
            dias_prazo = st.number_input(
                "Dias de Intervalo / Prazo (Dias) *",
                min_value=0,
                value=int(dados_edicao.get("dias", 0)),
                step=1,
                help="Quantidade de dias entre as parcelas ou prazo total da 1ª parcela.",
            )

        col_juros, col_multa, col_desconto = st.columns(3)
        with col_juros:
            perc_juros = st.number_input(
                "% Juros",
                min_value=0.0,
                max_value=100.0,
                value=float(dados_edicao.get("percentual_juros", 0.0) or 0.0),
                step=0.1,
                format="%.2f",
            )
        with col_multa:
            perc_multa = st.number_input(
                "% Multa",
                min_value=0.0,
                max_value=100.0,
                value=float(dados_edicao.get("percentual_multa", 0.0) or 0.0),
                step=0.1,
                format="%.2f",
            )
        with col_desconto:
            perc_desconto = st.number_input(
                "% Desconto",
                min_value=0.0,
                max_value=100.0,
                value=float(
                    dados_edicao.get("percentual_desconto", 0.0) or 0.0
                ),
                step=0.1,
                format="%.2f",
            )

        st.markdown("---")
        col_vazia, col_btn_salvar, col_btn_cancelar = st.columns([4, 1, 1])

        with col_btn_salvar:
            btn_salvar = st.form_submit_button(
                "Salvar", type="primary", use_container_width=True
            )

        with col_btn_cancelar:
            btn_cancelar = st.form_submit_button(
                "Cancelar", use_container_width=True
            )

    # Processamento do envio do formulário
    if btn_salvar:
        if not nome_condicao.strip():
            st.error("Preencha o campo obrigatório: Descrição da Condição.")
        else:
            if em_edicao:
                res = CondicaoPagamentoService.editar(
                    id_condicao=dados_edicao["id"],
                    condicao_pagamento=nome_condicao,
                    numero_parcelas=num_parcelas,
                    dias=dias_prazo,
                    percentual_juros=perc_juros,
                    percentual_multa=perc_multa,
                    percentual_desconto=perc_desconto,
                )
                st.success("Condição de pagamento atualizada com sucesso!")
                limpar_formulario()
                st.rerun()
            else:
                res = CondicaoPagamentoService.criar(
                    condicao_pagamento=nome_condicao,
                    numero_parcelas=num_parcelas,
                    dias=dias_prazo,
                    percentual_juros=perc_juros,
                    percentual_multa=perc_multa,
                    percentual_desconto=perc_desconto,
                )
                st.success("Nova condição de pagamento cadastrada com sucesso!")
                st.rerun()

    if btn_cancelar:
        limpar_formulario()
        st.rerun()