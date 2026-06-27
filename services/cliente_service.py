from database.connection import get_supabase

supabase = get_supabase()

class ClienteService:
    @staticmethod
    def listar_todos():
        # Trazemos dados da cidade e país para a listagem
        return supabase.table("cliente").select("*, cidade(nome, estado(uf)), pais(nome)").order("cliente").execute().data

    @staticmethod
    def criar(dados):
        return supabase.table("cliente").insert(dados).execute()

    @staticmethod
    def deletar(id_cliente):
        return supabase.table("cliente").delete().eq("id", id_cliente).execute()