from database.connection import get_supabase

supabase = get_supabase()

class ServicoService:
    @staticmethod
    def listar_todos():
        return supabase.table("servico").select("*").order("nome").execute().data

    @staticmethod
    def criar(nome, preco, duracao):
        data = {
            "nome": nome, 
            "preco": preco, 
            "duracao_minutos": duracao, 
            "ativo": True
        }
        return supabase.table("servico").insert(data).execute()

    @staticmethod
    def deletar(id_serv):
        return supabase.table("servico").delete().eq("id", id_serv).execute()