import pandas as pd
import streamlit as st
from services.condicaopag_service import CondicaoPagamentoService
from services.formpag_service import FormaPagamentoService

st.set_page_config(
    page_title="Condições de Pagamento", layout="wide", page_icon="💳"
)

# --- CARREGAMENTO DE DADOS AUXILIARES ---
formas_pag_db = FormaPagamentoService.listar_todas(apenas_ativos=True)
opcoes_forma_pagamento = (
    [fp["forma_pagamento"] for fp in formas_pag_db if fp.get("forma_pagamento")]
    if formas_pag_db else ["BOLETO", "PIX", "CARTÃO DE CRÉDITO", "TRANSFERÊNCIA", "DINHEIRO"]
)

# --- ESTADOS DA SESSÃO ---
if "modo_edicao" not in st.session_state:
    st.session_state.modo_edicao = False

if "condicao_em_edicao" not in st.session_state:
    st.session_state.condicao_em_edicao = None

if "parcelas_condicao" not in st.session_state:
    st.session_state.parcelas_condicao = []


def limpar_formulario():
    st.session_state.modo_edicao = False
    st.session_state.condicao_em_edicao = None
    st.session_state.parcelas_condicao = []


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

        if termo_busca:
            df = df[
                df["condicao_pagamento"]
                .str.lower()
                .str.contains(termo_busca.lower(), na=False)
            ]

        # Formatação das colunas
        df_exibicao = pd.DataFrame({
            "ID": df["id"],
            "Condição de Pagamento": df["condicao_pagamento"],
            "Parcelas": df["numero_parcelas"],
            "Juros (%)": df["percentual_juros"].apply(lambda x: f"{float(x or 0):.2f}%"),
            "Multa (%)": df["percentual_multa"].apply(lambda x: f"{float(x or 0):.2f}%"),
            "Desconto (%)": df["percentual_desconto"].apply(lambda x: f"{float(x or 0):.2f}%"),
            "Status": df["ativo"].apply(lambda a: "🟢 Ativo" if a else "🔴 Inativo"),
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

        if evento.selection.rows:
            idx = evento.selection.rows[0]
            registro_selecionado = df.iloc[idx].to_dict()

            st.markdown("---")
            col_info, col_btn_edit, col_btn_status = st.columns([4, 1, 1])

            with col_info:
                st.write(
                    f"**Selecionado:** {registro_selecionado['condicao_pagamento']} | "
                    f"**Parcelas:** {registro_selecionado['numero_parcelas']}x"
                )

            with col_btn_edit:
                if st.button("✏️ Editar", use_container_width=True, type="secondary"):
                    st.session_state.modo_edicao = True
                    st.session_state.condicao_em_edicao = registro_selecionado

                    parcelas = CondicaoPagamentoService.listar_parcelas(int(registro_selecionado["id"]))
                    st.session_state.parcelas_condicao = [
                        {
                            "DIAS": p["dias"],
                            "FORMA DE PAGAMENTO": p.get("forma_pagamento_nome") or "",
                            "% PARCELA": float(p["percentual"]),
                        }
                        for p in parcelas
                    ]

                    st.rerun()

            with col_btn_status:
                status_atual = registro_selecionado["ativo"]
                label_btn = "🔴 Desativar" if status_atual else "🟢 Ativar"
                if st.button(label_btn, use_container_width=True):
                    CondicaoPagamentoService.alternar_status(int(registro_selecionado["id"]))
                    st.toast("Status alterado com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhuma condição de pagamento encontrada.")

# -----------------------------------------------------------------------------
# TAB 2: FORMULÁRIO DE CADASTRO / EDIÇÃO (SEM ST.FORM)
# -----------------------------------------------------------------------------
with tab_cadastro:
    em_edicao = st.session_state.modo_edicao
    dados_edicao = st.session_state.condicao_em_edicao or {}

    with st.container(border=True):
        col_title, col_status = st.columns([5, 1])
        with col_title:
            if em_edicao:
                st.subheader(f"✏️ Editando: {dados_edicao.get('condicao_pagamento', '')}")
            else:
                st.subheader("Nova Condição de Pagamento")
        
        with col_status:
            status_condicao = st.toggle("Ativo", value=dados_edicao.get("ativo", True), key="tgl_status")

        # --- DADOS PRINCIPAIS ---
        nome_condicao = st.text_input(
            "Condição de pagamento *",
            value=dados_edicao.get("condicao_pagamento", ""),
            placeholder="Ex: 30/60/90 dias",
        )

        col_parc, col_dias1 = st.columns(2)
        with col_parc:
            num_parcelas_input = st.number_input(
                "Nº de Parcelas *",
                min_value=1,
                value=int(dados_edicao.get("numero_parcelas", 1)),
                step=1,
            )
        with col_dias1:
            primeira_parcela_dias = st.number_input(
                "1ª Parcela (dias) *",
                min_value=0,
                value=0, # Valor inicial padrão
                step=1,
            )

        col_juros, col_multa, col_desconto = st.columns(3)
        with col_juros:
            perc_juros = st.number_input(
                "Juros (%)", min_value=0.0, value=float(dados_edicao.get("percentual_juros", 0.0) or 0.0), step=0.01, format="%.2f"
            )
        with col_multa:
            perc_multa = st.number_input(
                "Multa (%)", min_value=0.0, value=float(dados_edicao.get("percentual_multa", 0.0) or 0.0), step=0.01, format="%.2f"
            )
        with col_desconto:
            perc_desconto = st.number_input(
                "Desconto (%)", min_value=0.0, value=float(dados_edicao.get("percentual_desconto", 0.0) or 0.0), step=0.01, format="%.2f"
            )

        st.markdown("---")
        
        # --- SEÇÃO DETALHADA DAS PARCELAS ---
        col_tit_parc, col_add_parc = st.columns([5, 1])
        with col_tit_parc:
            st.write("**Parcelas**")
            st.caption("A soma dos percentuais deve ser exatamente 100%.")
        with col_add_parc:
            if st.button("+ Adicionar parcela", use_container_width=True):
                # Adiciona uma nova linha em branco à lista
                st.session_state.parcelas_condicao.append({
                    "DIAS": 30 if len(st.session_state.parcelas_condicao) > 0 else primeira_parcela_dias,
                    "FORMA DE PAGAMENTO": opcoes_forma_pagamento[0] if opcoes_forma_pagamento else "",
                    "% PARCELA": 0.0
                })
                st.rerun()

        # Inicializa se estiver vazio, baseado no num_parcelas
        if not st.session_state.parcelas_condicao and not em_edicao:
            # Tenta inferir pelo nome se foi digitado (ex: "30/60/90")
            # ou apenas cria linhas em branco dividindo 100%
            perc_base = round(100.0 / num_parcelas_input, 2)
            
            for i in range(num_parcelas_input):
                # Arruma centavos da última parcela
                perc = perc_base if i < (num_parcelas_input - 1) else (100.0 - (perc_base * i))
                
                st.session_state.parcelas_condicao.append({
                    "DIAS": primeira_parcela_dias if i == 0 else (primeira_parcela_dias + (30*i)),
                    "FORMA DE PAGAMENTO": opcoes_forma_pagamento[0] if opcoes_forma_pagamento else "",
                    "% PARCELA": round(perc, 2)
                })

        # Exibição do Editor
        df_parcelas = pd.DataFrame(st.session_state.parcelas_condicao)
        
        # Auto-numeração
        if not df_parcelas.empty:
            df_parcelas.insert(0, "Nº", range(1, len(df_parcelas) + 1))
        else:
            df_parcelas = pd.DataFrame(columns=["Nº", "DIAS", "FORMA DE PAGAMENTO", "% PARCELA"])

        edited_parcelas = st.data_editor(
            df_parcelas,
            column_config={
                "Nº": st.column_config.NumberColumn("Nº", disabled=True),
                "DIAS": st.column_config.NumberColumn("DIAS", min_value=0, step=1),
                "FORMA DE PAGAMENTO": st.column_config.SelectboxColumn(
                    "FORMA DE PAGAMENTO",
                    help="Selecione a forma",
                    options=opcoes_forma_pagamento,
                    required=True,
                ),
                "% PARCELA": st.column_config.NumberColumn("% PARCELA", min_value=0.0, max_value=100.0, step=0.01, format="%.2f")
            },
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key="grid_edicao_parcelas"
        )

        # Atualiza state
        if not edited_parcelas.empty:
            # Remove a coluna N antes de salvar no state para evitar duplicidade
            state_to_save = edited_parcelas.drop(columns=["Nº"]).to_dict("records")
            st.session_state.parcelas_condicao = state_to_save

        # Validação do Total
        soma_percentual = edited_parcelas["% PARCELA"].sum() if not edited_parcelas.empty else 0.0
        
        col_vazia, col_total = st.columns([5, 1])
        with col_total:
            cor = "green" if abs(soma_percentual - 100.0) < 0.01 else "red"
            st.markdown(f"**Total:** <span style='color:{cor}'>{soma_percentual:.2f}%</span>", unsafe_allow_html=True)

        if abs(soma_percentual - 100.0) >= 0.01 and not edited_parcelas.empty:
            st.warning("⚠️ A soma dos percentuais das parcelas deve ser exatamente 100%.")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- BOTÕES DE AÇÃO ---
        col_vazia2, col_btn_salvar, col_btn_cancelar = st.columns([4, 1, 1])

        with col_btn_salvar:
            btn_salvar = st.button("Salvar", type="primary", use_container_width=True)

        with col_btn_cancelar:
            btn_cancelar = st.button("Cancelar", use_container_width=True)

    # --- LÓGICA DE SALVAR ---
    if btn_salvar:
        if not nome_condicao.strip():
            st.error("Preencha o campo obrigatório: Condição de pagamento.")
        elif abs(soma_percentual - 100.0) >= 0.01:
            st.error("Corrija as parcelas. A soma dos percentuais deve ser 100%.")
        elif len(st.session_state.parcelas_condicao) == 0:
            st.error("Adicione pelo menos uma parcela.")
        else:
            # Construindo o dicionário para enviar ao Service
            dados_cabecalho = {
                "condicao_pagamento": nome_condicao.strip().upper(),
                "numero_parcelas": len(st.session_state.parcelas_condicao), # Conta as linhas reais
                "percentual_juros": perc_juros,
                "percentual_multa": perc_multa,
                "percentual_desconto": perc_desconto,
                "ativo": status_condicao
            }
            
            parcelas_payload = []
            for p in st.session_state.parcelas_condicao:
                # Ignora linhas vazias adicionadas pelo data_editor
                if pd.isna(p.get("DIAS")) and pd.isna(p.get("% PARCELA")):
                    continue
                dias = p.get("DIAS")
                perc = p.get("% PARCELA")
                parcelas_payload.append({
                    "numero_parcela": len(parcelas_payload) + 1,
                    "dias": 0 if pd.isna(dias) else int(dias),
                    "forma_pagamento_nome": p.get("FORMA DE PAGAMENTO") or "",
                    "percentual": 0.0 if pd.isna(perc) else float(perc),
                })
            dados_cabecalho["numero_parcelas"] = len(parcelas_payload)

            if em_edicao:
                ok, res = CondicaoPagamentoService.editar_com_parcelas(
                    int(dados_edicao["id"]), dados_cabecalho, parcelas_payload
                )
                msg_sucesso = "Condição de pagamento atualizada com sucesso!"
            else:
                ok, res = CondicaoPagamentoService.criar_com_parcelas(
                    dados_cabecalho, parcelas_payload
                )
                msg_sucesso = "Nova condição de pagamento cadastrada com sucesso!"

            if ok:
                st.toast(msg_sucesso)
                limpar_formulario()
                st.rerun()
            else:
                st.error(f"Erro ao salvar: {res}")

    if btn_cancelar:
        limpar_formulario()
        st.rerun()