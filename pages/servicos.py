import streamlit as st
from services.servico_service import ServicoService

st.set_page_config(page_title="Gestão de Serviços", layout="wide")
st.title("✂️ Catálogo de Serviços")

with st.expander("Cadastrar Novo Serviço"):
    with st.form("form_servico"):
        nome = st.text_input("Nome do Serviço (Ex: Corte Masculino, Coloração)")
        
        col1, col2 = st.columns(2)
        preco = col1.number_input("Preço de Venda (R$)", min_value=0.0, step=5.0)
        duracao = col2.number_input("Duração Estimada (Minutos)", min_value=1, step=15, value=30)
        
        if st.form_submit_button("Salvar Serviço"):
            if nome:
                ServicoService.criar(nome, preco, duracao)
                st.success(f"Serviço '{nome}' cadastrado!")
                st.rerun()

servicos = ServicoService.listar_todos()
if servicos:
    st.subheader("Serviços Disponíveis")
    for s in servicos:
        c1, c2 = st.columns([0.8, 0.2])
        # Formata o tempo para facilitar a leitura (Ex: 90min -> 1h 30min)
        horas = s['duracao_minutos'] // 60
        mins = s['duracao_minutos'] % 60
        tempo_str = f"{horas}h {mins}min" if horas > 0 else f"{mins}min"
        
        c1.write(f"**{s['nome']}** | R$ {s['preco']:.2f} | ⏳ {tempo_str}")
        if c2.button("Excluir", key=f"srv_{s['id']}"):
            ServicoService.deletar(s['id'])
            st.rerun()