from database.connection import get_supabase

supabase = get_supabase()

class PaisService:
    @staticmethod
    def listar_todos(apenas_ativos=True):
        # Inicia a consulta na tabela de países
        query = supabase.table("pais").select("*")
        
        # Se for True, traz apenas os ativos. Se for False, traz todos (incluindo desativados)
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        response = query.order("nome").execute()
        return response.data

    @staticmethod
    def criar(nome, sigla, nacionalidade):
        data = {
            "nome": nome.strip().upper(),
            "sigla": sigla.strip().upper(),
            "nacionalidade": nacionalidade.strip().upper(),
            "ativo": True
        }
        return supabase.table("pais").insert(data).execute()

    @staticmethod
    def editar(id_pais, nome, sigla, nacionalidade):
        # Prepara os novos dados formatados
        data = {
            "nome": nome.strip().upper(),
            "sigla": sigla.strip().upper(),
            "nacionalidade": nacionalidade.strip().upper()
        }
        # Executa o update filtrando pelo ID do país
        return (
            supabase.table("pais")
            .update(data)
            .eq("id", id_pais)
            .execute()
        )

    @staticmethod
    def alternar_status(id_pais):
        # 1. Busca o status atual da flag 'ativo'
        busca = supabase.table("pais").select("ativo").eq("id", id_pais).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o status booleano (True vira False, e vice-versa)
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco com o status invertido
            return (
                supabase.table("pais")
                .update({"ativo": novo_status})
                .eq("id", id_pais)
                .execute()
            )
        return busca