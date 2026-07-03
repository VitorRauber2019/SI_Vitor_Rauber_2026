from database.connection import get_supabase

supabase = get_supabase()

class CidadeService:
    @staticmethod
    def listar_todos():
        # Traz o nome do estado e a UF para facilitar a visualização
        response = supabase.table("cidade").select("*, estado(nome, uf)").order("nome").execute()
        return response.data

    @staticmethod
    def criar(nome, codigo_ibge, estado_id):
        data = {
            "nome": nome.strip().upper(),
            "codigo_ibge": codigo_ibge,
            "estado_id": estado_id,
            "ativo": True
        }
        return supabase.table("cidade").insert(data).execute()

    @staticmethod
    def deletar(id_cidade):
        return supabase.table("cidade").delete().eq("id", id_cidade).execute()