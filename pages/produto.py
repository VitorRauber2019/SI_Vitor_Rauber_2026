import streamlit as st
from services.produto_service import ProdutoService
from services.marca_service import MarcaService
from services.categoria_service import CategoriaService
from services.unidade_medida_service import UnidadeMedidaService

st.set_page_config(page_title="Controle de Estoque", layout="wide")
st.title("📦 Gestão de Produtos e Insumos")

# Carregar dados para os selects (Dicionários para facilitar a busca do ID pelo nome)
marcas = {m['marca']: m['id'] for m in MarcaService.listar_todas()}
categorias = {c['categoria']: c['id'] for c in CategoriaService.listar_todas()}
unidades = {f"{u['unidade_medida']} ({u['sigla']})": u['id'] for u in UnidadeMedidaService.listar_todas()}

with st.expander("Cadastrar Novo Item", expanded=False):
    with st.form("form_produto", clear_on_submit=True):
        produto = st.text_input("Produto (Ex: Shampoo Hidratação Profunda 1L)")
        cod_barras = st.text_input("Código de Barras")
        
        col1, col2, col3 = st.columns(3)
        marca_sel = col1.selectbox("Marca", options=list(marcas.keys()))
        cat_sel = col2.selectbox("Categoria", options=list(categorias.keys()))
        un_sel = col3.selectbox("Unidade de Medida", options=list(unidades.keys()))
        
        col4, col5 = st.columns(2)
        v_compra = col4.number_input("Custo de Compra (R$)", min_value=0.0, step=1.0)
        v_venda = col5.number_input("Preço de Venda (R$)", min_value=0.0, step=1.0)
        
        col6, col7 = st.columns(2)
        qtd_atual = col6.number_input("Quantidade em Estoque", min_value=0.0)
        qtd_min = col7.number_input("Estoque Mínimo (Alerta)", min_value=0.0)
        
        if st.form_submit_button("Salvar Produto"):
            if produto and marcas and categorias and unidades:
                novo_prod = {
                    "nome": produto,
                    "codigo_barras": cod_barras,
                    "marca_id": marcas[marca_sel],
                    "categoria_id": categorias[cat_sel],
                    "unidade_medida_id": unidades[un_sel],
                    "valor_compra": v_compra,
                    "valor_venda": v_venda,
                    "quantidade_atual": qtd_atual,
                    "quantidade_minima": qtd_min,
                    "ativo": True
                }
                try:
                    ProdutoService.criar(novo_prod)
                    st.success("Produto adicionado ao estoque!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Verifique se o nome e as tabelas de apoio (Marca/Cat) estão preenchidos.")

# --- LISTAGEM COM ALERTA DE ESTOQUE ---
st.subheader("Itens em Prateleira")
produtos = ProdutoService.listar_todos()

if produtos:
    for p in produtos:
        # Lógica de alerta visual: Se estoque <= mínimo, destaca em vermelho/amarelo
        estoque_baixo = p['quantidade_atual'] <= p['quantidade_minima']
        
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([0.4, 0.2, 0.2, 0.2])
            
            c1.write(f"**{p['produto']}**")
            c1.caption(f"{p['marca']['marca']} | {p['categoria']['categoria']}")
            
            # Formatação de cores para o estoque
            qtd_str = f"{p['quantidade_atual']} {p['unidade_medida']['sigla']}"
            if estoque_baixo:
                c2.error(f"Estoque: {qtd_str}")
            else:
                c2.info(f"Estoque: {qtd_str}")
                
            c3.write(f"Venda: R$ {p['valor_venda']:.2f}")
            
            if c4.button("🗑️", key=f"del_p_{p['id']}"):
                ProdutoService.deletar(p['id'])
                st.rerun()
else:
    st.info("O estoque está vazio. Comece cadastrando um produto acima.")