from database.connection import get_supabase

supabase = get_supabase()

class ProdutoService:
    @staticmethod
    def listar_todos():
        # Fazemos o JOIN para trazer os nomes em vez de apenas os IDs
        query = "*, marca(marca), categoria(categoria), unidade_medida(sigla)"
        return supabase.table("produto").select(query).order("produto").execute().data

    @staticmethod
    def criar(dados):
        return supabase.table("produto").insert(dados).execute()

    @staticmethod
    def deletar(id_prod):
        return supabase.table("produto").delete().eq("id", id_prod).execute()