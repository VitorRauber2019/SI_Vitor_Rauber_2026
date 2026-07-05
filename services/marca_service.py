from database.connection import get_supabase

supabase = get_supabase()

class MarcaService:
    @staticmethod
    def listar_todas(apenas_ativos=True):
        # Inicia a consulta na tabela marca
        query = supabase.table("marca").select("*")
        
        # Filtra apenas pelas marcas ativas caso o parâmetro seja True
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        return query.order("marca").execute().data

    @staticmethod
    def criar(nome):
        return supabase.table("marca").insert({
            "marca": nome.strip().upper(), 
            "ativo": True
        }).execute()

    @staticmethod
    def editar(id_marca, nome):
        # Atualiza o campo 'marca' aplicando a formatação padrão
        return (
            supabase.table("marca")
            .update({"marca": nome.strip().upper()})
            .eq("id", id_marca)
            .execute()
        )

    @staticmethod
    def alternar_status(id_marca):
        # 1. Recupera o estado atual da flag 'ativo'
        busca = supabase.table("marca").select("ativo").eq("id", id_marca).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o valor booleano (True vira False e vice-versa)
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco de dados com o status invertido
            return (
                supabase.table("marca")
                .update({"ativo": novo_status})
                .eq("id", id_marca)
                .execute()
            )
        return busca