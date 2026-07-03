from database.connection import get_supabase

supabase = get_supabase()

class EstadoService:
    @staticmethod
    def listar_todos():
        # Faz um join simples para trazer o nome do país junto com o estado
        response = supabase.table("estado").select("*, pais(nome)").order("nome").execute()
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
    def deletar(id_estado):
        return supabase.table("estado").delete().eq("id", id_estado).execute()