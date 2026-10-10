import pandas as pd
import streamlit as st

TIPOS_VEICULO = ["CAMINHAO", "CARRETA", "TRUCK", "VAN", "UTILITARIO", "ONIBUS", "OUTRO"]


def resumo_veiculo(v):
    """Dados mínimos de um veículo guardados na lista de selecionados."""
    return {
        "id": int(v["id"]),
        "placa": v.get("placa") or "",
        "modelo": v.get("modelo") or "",
        "marca": v.get("marca") or "",
    }


def _nome_transportadora(v):
    t = v.get("transportadora")
    return t.get("razao_social", "") if isinstance(t, dict) else ""


def _adicionar(chave, veiculo):
    selecionados = st.session_state[chave]
    if all(s["id"] != veiculo["id"] for s in selecionados):
        selecionados.append(resumo_veiculo(veiculo))


def renderizar_veiculos_selecionados(chave, prefix, dentro_de_form=False):
    """Lista os veículos escolhidos para a transportadora, com opção de remover."""
    selecionados = st.session_state[chave]
    if not selecionados:
        st.caption("Nenhum veículo vinculado.")
        return

    for v in list(selecionados):
        c_txt, c_btn = st.columns([3, 1])
        marca = f" - {v['marca']}" if v.get("marca") else ""
        c_txt.text(f"• {v['placa']} / {v['modelo']}{marca}")
        botao = c_btn.form_submit_button if dentro_de_form else c_btn.button
        if botao("Remover", key=f"{prefix}_rm_veic_{v['id']}", use_container_width=True):
            st.session_state[chave] = [s for s in selecionados if s["id"] != v["id"]]
            # Dentro de um st.dialog o rerun do fragmento mantém o modal aberto
            if dentro_de_form:
                st.rerun()
            st.rerun(scope="fragment")


def campos_novo_veiculo(prefix):
    """Campos do cadastro de veículo. Retorna o dicionário pronto para o Supabase."""
    c_placa, c_modelo, c_marca = st.columns(3)
    placa = c_placa.text_input("Placa *", max_chars=10, placeholder="AAA0A00", key=f"{prefix}_placa")
    modelo = c_modelo.text_input("Modelo *", key=f"{prefix}_modelo")
    marca = c_marca.text_input("Marca", key=f"{prefix}_marca")

    c_tipo, c_ano, c_cap = st.columns(3)
    tipo = c_tipo.selectbox("Tipo", TIPOS_VEICULO, key=f"{prefix}_tipo")
    ano = c_ano.number_input("Ano", min_value=0, max_value=2100, value=0, step=1, key=f"{prefix}_ano")
    capacidade = c_cap.number_input("Capacidade (kg)", min_value=0.0, value=0.0, step=100.0, key=f"{prefix}_cap")

    c_renavam, c_rntrc = st.columns(2)
    renavam = c_renavam.text_input("RENAVAM", key=f"{prefix}_renavam")
    rntrc = c_rntrc.text_input("RNTRC", key=f"{prefix}_rntrc")

    return {
        "placa": placa.strip().replace("-", "").replace(" ", ""),
        "modelo": modelo.strip(),
        "marca": marca.strip() or None,
        "tipo": tipo,
        "ano": int(ano) or None,
        "capacidade_kg": capacidade,
        "renavam": renavam.strip() or None,
        "rntrc": rntrc.strip() or None,
    }


def renderizar_gerenciador_veiculos(service, chave, prefix, rerun_scope="fragment"):
    """Abas para escolher veículos existentes ou cadastrar novos e adicioná-los à lista."""
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Veículo", "➕ Novo Veículo"])

    with tab_sel:
        busca = st.text_input("Buscar", placeholder="Placa, modelo ou marca...", key=f"{prefix}_busca_veic")
        ids_selecionados = {s["id"] for s in st.session_state[chave]}
        veiculos = [
            v for v in service.listar_todos(busca=busca.strip() or None, apenas_ativos=True)
            if v["id"] not in ids_selecionados
        ]

        if not veiculos:
            st.info("Nenhum veículo disponível.")
        else:
            df_v = pd.DataFrame([
                {
                    "ID": v["id"],
                    "Placa": v.get("placa") or "",
                    "Modelo": v.get("modelo") or "",
                    "Marca": v.get("marca") or "",
                    "Tipo": v.get("tipo") or "",
                    "Transportadora Atual": _nome_transportadora(v),
                }
                for v in veiculos
            ])
            event = st.dataframe(
                df_v,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                # Muda a key quando a lista muda, para não manter a seleção de outra linha
                key=f"{prefix}_grid_veiculos_{'_'.join(map(str, sorted(ids_selecionados)))}",
            )

            if event.selection.rows and event.selection.rows[0] < len(veiculos):
                escolhido = veiculos[event.selection.rows[0]]
                atual = _nome_transportadora(escolhido)
                if atual:
                    st.warning(f"Este veículo está vinculado a {atual}. Ao salvar, ele será transferido.")
                if st.button("🎯 Selecionar Veículo", type="primary", use_container_width=True, key=f"{prefix}_btn_sel_veic"):
                    _adicionar(chave, escolhido)
                    st.rerun(scope=rerun_scope)

    with tab_cad:
        # A versão entra nas keys para limpar os campos depois de salvar
        chave_versao = f"{prefix}_versao_cad_veic"
        versao = st.session_state.setdefault(chave_versao, 0)
        with st.container(border=True):
            dados = campos_novo_veiculo(prefix=f"{prefix}_cad_veic_{versao}")
            if st.button("Salvar e Adicionar Veículo", type="primary", use_container_width=True, key=f"{prefix}_btn_save_veic"):
                if dados["placa"] and dados["modelo"]:
                    sucesso, res = service.criar(dados)
                    if sucesso:
                        _adicionar(chave, res)
                        st.session_state[chave_versao] += 1
                        st.rerun(scope=rerun_scope)
                    else:
                        st.error(res)
                else:
                    st.error("Informe a Placa e o Modelo do veículo.")
