from database.connection import get_supabase

supabase = get_supabase()

class CidadeService:
    @staticmethod
    def listar_todos(apenas_ativos=True):
        # Inicia a consulta trazendo os dados da cidade e do estado
        query = supabase.table("cidade").select("*, estado(nome, uf)")
        
        # Se o parâmetro for True, filtra apenas os ativos. 
        # Se for False, traz tudo (útil para telas de lixeira ou administração)
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        response = query.order("nome").execute()
        return response.data

    @staticmethod
    def criar(nome, estado_id):
        data = {
            "nome": nome.strip().upper(),
            "estado_id": estado_id,
            "ativo": True
        }
        return supabase.table("cidade").insert(data).execute()

    @staticmethod
    def editar(id_cidade, nome, estado_id):
        data = {
            "nome": nome.strip().upper(),
            "estado_id": estado_id
        }
        return supabase.table("cidade").update(data).eq("id", id_cidade).execute()

    @staticmethod
    def alternar_status(id_cidade):
        # 1. Busca o status atual da flag 'ativo' no banco de dados
        busca = supabase.table("cidade").select("ativo").eq("id", id_cidade).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o status usando o operador 'not'
            # Se era True (ativo), vira False (deletado). Se era False, vira True (reativado).
            novo_status = not status_atual
            
            # 3. Atualiza o banco de dados com o novo estado invertido
            return (
                supabase.table("cidade")
                .update({"ativo": novo_status})
                .eq("id", id_cidade)
                .execute()
            )
        return busca