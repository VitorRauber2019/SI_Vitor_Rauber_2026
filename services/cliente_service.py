from database.connection import get_supabase

supabase = get_supabase()

class ClienteService:
    @staticmethod
    def listar_todos(apenas_ativos=True):
        query_select = "*, cidade(nome, estado(uf))"
        query = supabase.table("cliente").select(query_select)
        
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        return query.order("cliente").execute().data

    @staticmethod
    def criar(dados):
        # Tratamento dinâmico: e-mail em lowercase, resto em uppercase
        dados_tratados = {
            chave: (valor.strip().lower() if chave == "email" else valor.strip().upper()) 
            if isinstance(valor, str) else valor 
            for chave, valor in dados.items()
        }
        dados_tratados["ativo"] = True
        return supabase.table("cliente").insert(dados_tratados).execute()

    @staticmethod
    def editar(id_cliente, dados):
        # Tratamento dinâmico: e-mail em lowercase, resto em uppercase
        dados_tratados = {
            chave: (valor.strip().lower() if chave == "email" else valor.strip().upper()) 
            if isinstance(valor, str) else valor 
            for chave, valor in dados.items()
        }
        return (
            supabase.table("cliente")
            .update(dados_tratados)
            .eq("id", id_cliente)
            .execute()
        )

    @staticmethod
    def alternar_status(id_cliente):
        busca = supabase.table("cliente").select("ativo").eq("id", id_cliente).execute()
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            novo_status = not status_atual
            return (
                supabase.table("cliente")
                .update({"ativo": novo_status})
                .eq("id", id_cliente)
                .execute()
            )
        return busca