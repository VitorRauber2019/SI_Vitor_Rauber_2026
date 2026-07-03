from database.connection import get_supabase

supabase = get_supabase()

class ClienteService:
    @staticmethod
    def listar_todos():
        # Trazemos dados da cidade e país para a listagem
        return supabase.table("cliente").select("*, cidade(nome, estado(uf)), pais(nome)").order("cliente").execute().data

    @staticmethod
    def criar(dados):
        # Trata o dicionário dynamicamente: o que for texto vira caixa alta e remove espaços inúteis
        dados_tratados = {
            chave: valor.strip().upper() if isinstance(valor, str) else valor 
            for chave, valor in dados.items()
        }
        return supabase.table("cliente").insert(dados_tratados).execute()

    @staticmethod
    def deletar(id_cliente):
        return supabase.table("cliente").delete().eq("id", id_cliente).execute()