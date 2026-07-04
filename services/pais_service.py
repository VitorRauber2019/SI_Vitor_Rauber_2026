from database.connection import get_supabase

supabase = get_supabase()

class PaisService:
    @staticmethod
    def listar_todos():
        # Busca países ordenados por nome
        response = supabase.table("pais").select("*").order("nome").execute()
        return response.data

    @staticmethod
    def criar(nome, codigo, sigla, nacionalidade):
        data = {
            "nome": nome.strip().upper(),
            "codigo": codigo,
            "sigla": sigla.strip().upper(),
            "nacionalidade": nacionalidade.strip().upper(),
            "ativo": True
        }
        return supabase.table("pais").insert(data).execute()

    @staticmethod
    def deletar(id_pais):
        return supabase.table("pais").delete().eq("id", id_pais).execute()