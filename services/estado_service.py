from database.connection import get_supabase

supabase = get_supabase()

class EstadoService:
    @staticmethod
    def listar_todos(apenas_ativos=True):
        # Faz um join simples para trazer o nome do país junto com o estado
        query = supabase.table("estado").select("*, pais(nome)")
        
        # Filtra por ativos se o parâmetro for True
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        response = query.order("nome").execute()
        return response.data

    @staticmethod
    def criar(nome, uf, pais_id):
        data = {
            "nome": nome.strip().upper(),
            "uf": uf.strip().upper(),
            "pais_id": pais_id,
            "ativo": True
        }
        return supabase.table("estado").insert(data).execute()

    @staticmethod
    def editar(id_estado, nome, uf, pais_id):
        # Prepara os dados do estado com o tratamento de string padrão
        data = {
            "nome": nome.strip().upper(),
            "uf": uf.strip().upper(),
            "pais_id": pais_id
        }
        # Executa a atualização filtrando pelo ID do estado
        return (
            supabase.table("estado")
            .update(data)
            .eq("id", id_estado)
            .execute()
        )

    @staticmethod
    def alternar_status(id_estado):
        # 1. Recupera o estado atual da flag 'ativo'
        busca = supabase.table("estado").select("ativo").eq("id", id_estado).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o booleano (Ativo vira Desativado e vice-versa)
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco
            return (
                supabase.table("estado")
                .update({"ativo": novo_status})
                .eq("id", id_estado)
                .execute()
            )
        return busca