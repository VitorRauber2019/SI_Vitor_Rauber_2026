from database.connection import get_supabase

supabase = get_supabase()

class MarcaService:
    @staticmethod
    def listar_todas():
        return supabase.table("marca").select("*").order("marca").execute().data

    @staticmethod
    def criar(nome):
        return supabase.table("marca").insert({"marca": nome.strip().upper(), "ativo": True}).execute()

    @staticmethod
    def deletar(id_marca):
        return supabase.table("marca").delete().eq("id", id_marca).execute()