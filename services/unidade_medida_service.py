from database.connection import get_supabase

supabase = get_supabase()

class UnidadeMedidaService:
    @staticmethod
    def listar_todas():
        return supabase.table("unidade_medida").select("*").order("unidade_medida").execute().data

    @staticmethod
    def criar(nome, sigla):
        return supabase.table("unidade_medida").insert({"unidade_medida": nome, "sigla": sigla}).execute()

    @staticmethod
    def deletar(id_un):
        return supabase.table("unidade_medida").delete().eq("id", id_un).execute()