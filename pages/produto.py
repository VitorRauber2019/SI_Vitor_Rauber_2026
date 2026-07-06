import streamlit as st
import pandas as pd
from services.produto_service import ProdutoService
from services.marca_service import MarcaService
from services.categoria_service import CategoriaService
from services.unidade_medida_service import UnidadeMedidaService

st.set_page_config(page_title="Controle de Estoque", layout="wide")
st.title("📦 Gestão de Produtos e Insumos")

# --- INICIALIZAÇÃO DE ESTADOS DE SESSÃO ---
if "produto_para_editar" not in st.session_state:
    st.session_state.produto_para_editar = None

if "marca_selecionada" not in st.session_state:
    st.session_state.marca_selecionada = None

if "categoria_selecionada" not in st.session_state:
    st.session_state.categoria_selecionada = None

if "unidade_selecionada" not in st.session_state:
    st.session_state.unidade_selecionada = None

# Controles internos de edição inline dentro dos popups/dialogs
if "marca_inline_editar" not in st.session_state:
    st.session_state.marca_inline_editar = None

if "categoria_inline_editar" not in st.session_state:
    st.session_state.categoria_inline_editar = None

if "unidade_inline_editar" not in st.session_state:
    st.session_state.unidade_inline_editar = None


# --- MODAL: GERENCIAR MARCAS ---
@st.dialog("Gerenciar Marcas", width="large")
def gerenciar_marcas_modal():
    tab_sel, tab_cad = st.tabs(["🔍 Marca", "➕ Nova Marca"])
    with tab_sel:
        exibir_m_desat = st.checkbox("👁️ Exibir marcas desativadas", value=False, key="modal_chk_m_desat")
        marcas = MarcaService.listar_todas(apenas_ativos=not exibir_m_desat)
        if not marcas:
            st.info("Nenhuma marca cadastrada.")
        else:
            dados_m = [{"id": m["id"], "Marca": m["marca"], "Status": "🟢 Ativa" if m.get("ativo", True) else "🔴 Desativada"} for m in marcas]
            df_m = pd.DataFrame(dados_m)
            event = st.dataframe(df_m, column_config={"id": st.column_config.NumberColumn("ID", width="small")}, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="modal_grid_marcas")
            
            if event.selection.rows:
                escolhido = df_m.iloc[event.selection.rows[0]]
                st.write("")
                c_sel, c_edit, c_del = st.columns(3)
                
                if escolhido["Status"] == "🟢 Ativa":
                    if c_sel.button("🎯 Selecionar", use_container_width=True, key="modal_btn_sel_m"):
                        st.session_state.marca_selecionada = {"label": escolhido["Marca"], "id": int(escolhido["id"])}
                        st.rerun()
                else:
                    c_sel.button("🎯 Bloqueado", disabled=True, use_container_width=True)
                    
                if c_edit.button("✏️ Editar", use_container_width=True, key="modal_btn_edit_m"):
                    st.session_state.marca_inline_editar = {"id": int(escolhido["id"]), "marca": escolhido["Marca"]}
                    st.rerun()
                    
                ativa = escolhido["Status"] == "🟢 Ativa"
                if c_del.button("❌ Desativar" if ativa else "🔄 Reativar", type="primary" if ativa else "secondary", use_container_width=True, key="modal_btn_del_m"):
                    MarcaService.alternar_status(int(escolhido["id"]))
                    st.rerun()
            
            if st.session_state.marca_inline_editar is not None:
                st.write("---")
                edit_m_nome = st.text_input("Modificar Nome da Marca", value=st.session_state.marca_inline_editar["marca"])
                ce1, ce2 = st.columns(2)
                if ce1.button("Salvar Alteração", type="primary", use_container_width=True, key="modal_btn_save_m_inline"):
                    MarcaService.editar(st.session_state.marca_inline_editar["id"], edit_m_nome)
                    st.session_state.marca_inline_editar = None
                    st.rerun()
                if ce2.button("Cancelar", use_container_width=True, key="modal_btn_canc_m_inline"):
                    st.session_state.marca_inline_editar = None
                    st.rerun()
    with tab_cad:
        nome_m = st.text_input("Nome da Nova Marca", key="modal_input_nova_m")
        if st.button("Salvar Marca", type="primary"):
            if nome_m:
                MarcaService.criar(nome_m)
                st.success("Marca cadastrada!")
                st.rerun()


# --- MODAL: GERENCIAR CATEGORIAS ---
@st.dialog("Gerenciar Categorias", width="large")
def gerenciar_categorias_modal():
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Categoria", "➕ Nova Categoria"])
    with tab_sel:
        exibir_c_desat = st.checkbox("👁️ Exibir categorias desativadas", value=False, key="modal_chk_c_desat")
        categorias = CategoriaService.listar_todas(apenas_ativos=not exibir_c_desat)
        if not categorias:
            st.info("Nenhuma categoria cadastrada.")
        else:
            dados_c = [{"id": c["id"], "Categoria": c["categoria"], "Status": "🟢 Ativa" if c.get("ativo", True) else "🔴 Desativada"} for c in categorias]
            df_c = pd.DataFrame(dados_c)
            event = st.dataframe(df_c, column_config={"id": st.column_config.NumberColumn("ID", width="small")}, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="modal_grid_categorias")
            
            if event.selection.rows:
                escolhido = df_c.iloc[event.selection.rows[0]]
                st.write("")
                c_sel, c_edit, c_del = st.columns(3)
                
                if escolhido["Status"] == "🟢 Ativa":
                    if c_sel.button("🎯 Selecionar", use_container_width=True, key="modal_btn_sel_c"):
                        st.session_state.categoria_selecionada = {"label": escolhido["Categoria"], "id": int(escolhido["id"])}
                        st.rerun()
                else:
                    c_sel.button("🎯 Bloqueado", disabled=True, use_container_width=True)
                    
                if c_edit.button("✏️ Editar", use_container_width=True, key="modal_btn_edit_c"):
                    st.session_state.categoria_inline_editar = {"id": int(escolhido["id"]), "categoria": escolhido["Categoria"]}
                    st.rerun()
                    
                ativa = escolhido["Status"] == "🟢 Ativa"
                if c_del.button("❌ Desativar" if ativa else "🔄 Reativar", type="primary" if ativa else "secondary", use_container_width=True, key="modal_btn_del_c"):
                    CategoriaService.alternar_status(int(escolhido["id"]))
                    st.rerun()
                    
            if st.session_state.categoria_inline_editar is not None:
                st.write("---")
                edit_c_nome = st.text_input("Modificar Nome da Categoria", value=st.session_state.categoria_inline_editar["categoria"])
                cc1, cc2 = st.columns(2)
                if cc1.button("Salvar Alteração", type="primary", use_container_width=True, key="modal_btn_save_c_inline"):
                    CategoriaService.editar(st.session_state.categoria_inline_editar["id"], edit_c_nome)
                    st.session_state.categoria_inline_editar = None
                    st.rerun()
                if cc2.button("Cancelar", use_container_width=True, key="modal_btn_canc_c_inline"):
                    st.session_state.categoria_inline_editar = None
                    st.rerun()
    with tab_cad:
        nome_c = st.text_input("Nome da Nova Categoria", key="modal_input_nova_c")
        if st.button("Salvar Categoria", type="primary"):
            if nome_c:
                CategoriaService.criar(nome_c)
                st.success("Categoria cadastrada!")
                st.rerun()


# --- MODAL: GERENCIAR UNIDADES DE MEDIDA ---
@st.dialog("Gerenciar Unidades de Medida", width="large")
def gerenciar_unidades_modal():
    tab_sel, tab_cad = st.tabs(["🔍 Selecionar Unidade", "➕ Nova Unidade"])
    with tab_sel:
        exibir_u_desat = st.checkbox("👁️ Exibir unidades desativadas", value=False, key="modal_chk_u_desat")
        unidades = UnidadeMedidaService.listar_todas(apenas_ativos=not exibir_u_desat)
        if not unidades:
            st.info("Nenhuma unidade cadastrada.")
        else:
            dados_u = [{"id": u["id"], "Unidade": u["unidade_medida"], "Sigla": u["sigla"], "Status": "🟢 Ativa" if u.get("ativo", True) else "🔴 Desativada"} for u in unidades]
            df_u = pd.DataFrame(dados_u)
            event = st.dataframe(df_u, column_config={"id": st.column_config.NumberColumn("ID", width="small")}, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="modal_grid_unidades")
            
            if event.selection.rows:
                escolhido = df_u.iloc[event.selection.rows[0]]
                st.write("")
                c_sel, c_edit, c_del = st.columns(3)
                
                if escolhido["Status"] == "🟢 Ativa":
                    if c_sel.button("🎯 Selecionar", use_container_width=True, key="modal_btn_sel_u"):
                        st.session_state.unidade_selecionada = {"label": f"{escolhido['Unidade']} ({escolhido['Sigla']})", "id": int(escolhido["id"])}
                        st.rerun()
                else:
                    c_sel.button("🎯 Bloqueado", disabled=True, use_container_width=True)
                    
                if c_edit.button("✏️ Editar", use_container_width=True, key="modal_btn_edit_u"):
                    st.session_state.unidade_inline_editar = {"id": int(escolhido["id"]), "unidade_medida": escolhido["Unidade"], "sigla": escolhido["Sigla"]}
                    st.rerun()
                    
                ativa = escolhido["Status"] == "🟢 Ativa"
                if c_del.button("❌ Desativar" if ativa else "🔄 Reativar", type="primary" if ativa else "secondary", use_container_width=True, key="modal_btn_del_u"):
                    UnidadeMedidaService.alternar_status(int(escolhido["id"]))
                    st.rerun()
                    
            if st.session_state.unidade_inline_editar is not None:
                st.write("---")
                cu1, cu2 = st.columns([0.7, 0.3])
                edit_u_nome = cu1.text_input("Nome", value=st.session_state.unidade_inline_editar["unidade_medida"])
                edit_u_sigla = cu2.text_input("Sigla", value=st.session_state.unidade_inline_editar["sigla"], max_chars=3)
                cu_b1, cu_b2 = st.columns(2)
                if cu_b1.button("Salvar Alteração", type="primary", use_container_width=True, key="modal_btn_save_u_inline"):
                    UnidadeMedidaService.editar(st.session_state.unidade_inline_editar["id"], edit_u_nome, edit_u_sigla)
                    st.session_state.unidade_inline_editar = None
                    st.rerun()
                if cu_b2.button("Cancelar", use_container_width=True, key="modal_btn_canc_u_inline"):
                    st.session_state.unidade_inline_editar = None
                    st.rerun()
    with tab_cad:
        col_n, col_s = st.columns([0.7, 0.3])
        nome_u = col_n.text_input("Nome da Nova Unidade", key="modal_input_nova_u")
        sigla_u = col_s.text_input("Sigla (Ex: KG)", max_chars=3, key="modal_input_nova_s")
        if st.button("Salvar Unidade", type="primary", key="modal_btn_save_u_new"):
            if nome_u and sigla_u:
                UnidadeMedidaService.criar(nome_u, sigla_u)
                st.success("Unidade cadastrada!")
                st.rerun()


# --- TELA PRINCIPAL: FORMULÁRIO DINÂMICO (CADASTRO / EDIÇÃO) ---
modo_edicao = st.session_state.produto_para_editar is not None
titulo_formulario = "✏️ Editar Produto" if modo_edicao else "✨ Cadastrar Novo Item"

with st.expander(titulo_formulario, expanded=modo_edicao):
    prod_padrao = st.session_state.produto_para_editar["produto"] if modo_edicao else ""
    cod_padrao = st.session_state.produto_para_editar["codigo_barras"] if modo_edicao else ""
    v_compra_padrao = float(st.session_state.produto_para_editar["valor_compra"]) if modo_edicao else 0.0
    v_venda_padrao = float(st.session_state.produto_para_editar["valor_venda"]) if modo_edicao else 0.0
    # 💡 MODIFICADO: Cast de float para int para a quantidade padrão de edição
    qtd_atual_padrao = int(st.session_state.produto_para_editar["quantidade_atual"]) if modo_edicao else 0

    produto = st.text_input("Produto (Ex: Shampoo Hidratação Profunda 1L)", value=prod_padrao)
    cod_barras = st.text_input("Código de Barras", value=cod_padrao)
    
    col_m, col_c, col_u = st.columns(3)
    
    m_atual = st.session_state.marca_selecionada
    col_m.write("**Marca**")
    if col_m.button(m_atual["label"] if m_atual else "Marca", icon="🏷️", use_container_width=True):
        gerenciar_marcas_modal()
        
    c_atual = st.session_state.categoria_selecionada
    col_c.write("**Categoria**")
    if col_c.button(c_atual["label"] if c_atual else "Categoria", icon="📁", use_container_width=True):
        gerenciar_categorias_modal()
        
    u_atual = st.session_state.unidade_selecionada
    col_u.write("**Unidade de Medida**")
    if col_u.button(u_atual["label"] if u_atual else "Unidade de Medida", icon="⚖️", use_container_width=True):
        gerenciar_unidades_modal()
    
    st.write("")
    col4, col5, col6 = st.columns(3)
    v_compra = col4.number_input("Custo de Compra (R$)", min_value=0.0, step=1.0, value=v_compra_padrao)
    v_venda = col5.number_input("Preço de Venda (R$)", min_value=0.0, step=1.0, value=v_venda_padrao)
    # 💡 MODIFICADO: min_value=0 e step=1 (valores inteiros) força o componente a operar estritamente como int
    qtd_atual = col6.number_input("Quantidade em Estoque", min_value=0, step=1, value=qtd_atual_padrao)
    
    st.write("")
    col_btn_salvar, col_btn_cancelar, _ = st.columns([0.15, 0.15, 0.7])
    
    novo_prod = {
        "produto": produto,
        "codigo_barras": cod_barras,
        "marca_id": m_atual["id"] if m_atual else None,
        "categoria_id": c_atual["id"] if c_atual else None,
        "unidade_medida_id": u_atual["id"] if u_atual else None,
        "valor_compra": v_compra,
        "valor_venda": v_venda,
        "quantidade_atual": int(qtd_atual), # 💡 MODIFICADO: Garantia extra forçando int no dicionário
    }

    if modo_edicao:
        if col_btn_salvar.button("Salvar Alterações", type="primary", use_container_width=True):
            if produto and m_atual and c_atual and u_atual:
                ProdutoService.editar(st.session_state.produto_para_editar["id"], novo_prod)
                st.success("Produto updated!")
                st.session_state.produto_para_editar = None
                st.session_state.marca_selecionada = None
                st.session_state.categoria_selecionada = None
                st.session_state.unidade_selecionada = None
                st.rerun()
            else:
                st.error("Preencha a descrição do produto e selecione todas as tabelas de apoio.")
        if col_btn_cancelar.button("Cancelar", use_container_width=True):
            st.session_state.produto_para_editar = None
            st.session_state.marca_selecionada = None
            st.session_state.categoria_selecionada = None
            st.session_state.unidade_selecionada = None
            st.rerun()
    else:
        if col_btn_salvar.button("Salvar Produto", type="primary", use_container_width=True):
            if produto and m_atual and c_atual and u_atual:
                ProdutoService.criar(novo_prod)
                st.success("Produto adicionado ao estoque!")
                st.session_state.marca_selecionada = None
                st.session_state.categoria_selecionada = None
                st.session_state.unidade_selecionada = None
                st.rerun()
            else:
                st.error("Preencha a descrição do produto e selecione todas as tabelas de apoio.")

# --- FILTRO DE EXIBIÇÃO ---
st.write("")
exibir_desativados = st.checkbox("👁️ Exibir itens desativados (Soft Deleted)", value=False)

# --- LISTAGEM EM GRID INTERATIVO ---
produtos = ProdutoService.listar_todos(apenas_ativos=not exibir_desativados)

if produtos:
    st.subheader("📊 Itens em Prateleira")
    
    dados_grid = []
    for p in produtos:
        m_rel = p.get('marca', {})
        c_rel = p.get('categoria', {})
        u_rel = p.get('unidade_medida', {})
        
        dados_grid.append({
            "id": p['id'],
            "Produto": p['produto'],
            "Código de Barras": p.get('codigo_barras', 'N/A'),
            "Marca": m_rel.get('marca', 'N/A') if m_rel else 'N/A',
            "Categoria": c_rel.get('categoria', 'N/A') if c_rel else 'N/A',
            # 💡 MODIFICADO: Cast para int garante exibição limpa sem ".0" na tabela
            "Estoque": f"{int(p['quantidade_atual'])} {u_rel.get('sigla', '') if u_rel else ''}", 
            "Preço Venda": f"R$ {p['valor_venda']:.2f}",
            "Status": "🟢 Ativo" if p.get('ativo', True) else "🔴 Desativado",
            "marca_id": p.get('marca_id'),
            "categoria_id": p.get('categoria_id'),
            "unidade_medida_id": p.get('unidade_medida_id'),
            "valor_compra": p.get('valor_compra')
        })
        
    df_produtos = pd.DataFrame(dados_grid)
    
    evento_grid = st.dataframe(
        df_produtos,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "marca_id": None, "categoria_id": None, "unidade_medida_id": None, "valor_compra": None,
            "Produto": st.column_config.TextColumn("Produto", width="large"),
            "Status": st.column_config.TextColumn("Status", width="small")
        },
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )
    
    if evento_grid.selection.rows:
        idx_selecionado = evento_grid.selection.rows[0]
        prod_escolhido = df_produtos.iloc[idx_selecionado]
        
        st.write("")
        c_aviso, c_edit, c_del = st.columns([0.5, 0.25, 0.25])
        c_aviso.info(f"Item Selecionado: ID **{prod_escolhido['id']}** - **{prod_escolhido['Produto']}**")
        
        # 1. BOTÃO EDITAR SELECIONADO
        if c_edit.button("✏️ Editar Selecionado", use_container_width=True):
            st.session_state.produto_para_editar = {
                "id": int(prod_escolhido['id']),
                "produto": prod_escolhido['Produto'],
                "codigo_barras": prod_escolhido['Código de Barras'],
                "valor_compra": prod_escolhido['valor_compra'],
                "valor_venda": float(prod_escolhido['Preço Venda'].replace("R$ ", "")),
                "quantidade_atual": int(prod_escolhido['Estoque'].split()[0])
            }
            # Popula as flags das tabelas auxiliares para carregar nos botões de Popover
            st.session_state.marca_selecionada = {"id": int(prod_escolhido['marca_id']), "label": prod_escolhido['Marca']}
            st.session_state.categoria_selecionada = {"id": int(prod_escolhido['categoria_id']), "label": prod_escolhido['Categoria']}
            st.session_state.unidade_selecionada = {"id": int(prod_escolhido['unidade_medida_id']), "label": prod_escolhido['Estoque'].split()[1]}
            st.rerun()
            
        # 2. BOTÃO SOFT DELETE (ALTERNAR STATUS LOGICO)
        esta_ativo = "🟢 Ativo" in prod_escolhido['Status']
        texto_botao = "❌ Desativar" if esta_ativo else "🔄 Reativar"
        cor_botao = "primary" if esta_ativo else "secondary"
        
        if c_del.button(texto_botao, type=cor_botao, use_container_width=True):
            ProdutoService.alternar_status(int(prod_escolhido['id']))
            st.success("Status alterado com sucesso!")
            st.rerun()
else:
    st.info("O estoque está vazio ou nenhum item corresponde aos filtros aplicados.")