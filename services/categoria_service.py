from database.connection import get_supabase

supabase = get_supabase()

class CategoriaService:
    @staticmethod
    def listar_todas():
        return supabase.table("categoria").select("*").order("categoria").execute().data

    @staticmethod
    def criar(nome):
        return supabase.table("categoria").insert({"categoria": nome.strip().upper(), "ativo": True}).execute()

    @staticmethod
    def deletar(id_cat):
        return supabase.table("categoria").delete().eq("id", id_cat).execute()