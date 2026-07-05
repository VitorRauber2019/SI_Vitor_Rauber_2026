from database.connection import get_supabase

supabase = get_supabase()

class CategoriaService:
    @staticmethod
    def listar_todas(apenas_ativos=True):
        # Inicia a consulta na tabela categoria
        query = supabase.table("categoria").select("*")
        
        # Filtra apenas pelas categorias ativas caso o parâmetro seja True
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        return query.order("categoria").execute().data

    @staticmethod
    def criar(nome):
        return supabase.table("categoria").insert({
            "categoria": nome.strip().upper(), 
            "ativo": True
        }).execute()

    @staticmethod
    def editar(id_cat, nome):
        # Atualiza o campo 'categoria' aplicando a formatação padrão
        return (
            supabase.table("categoria")
            .update({"categoria": nome.strip().upper()})
            .eq("id", id_cat)
            .execute()
        )

    @staticmethod
    def alternar_status(id_cat):
        # 1. Recupera o estado atual da flag 'ativo'
        busca = supabase.table("categoria").select("ativo").eq("id", id_cat).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o valor booleano
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco de dados com o status invertido
            return (
                supabase.table("categoria")
                .update({"ativo": novo_status})
                .eq("id", id_cat)
                .execute()
            )
        return busca