from database.connection import get_supabase

supabase = get_supabase()

class ProdutoService:
    @staticmethod
    def listar_todos(apenas_ativos=True):
        # Fazemos o JOIN para trazer os nomes em vez de apenas os IDs
        query_select = "*, marca(marca), categoria(categoria), unidade_medida(sigla)"
        query = supabase.table("produto").select(query_select)
        
        # Filtra por produtos ativos caso o parâmetro seja True
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        return query.order("produto").execute().data

    @staticmethod
    def criar(dados):
        # Trata o dicionário dinamicamente: o que for texto vira caixa alta e remove espaços inúteis
        dados_tratados = {
            chave: valor.strip().upper() if isinstance(valor, str) else valor 
            for chave, valor in dados.items()
        }
        # Garante que o produto inicie com o status ativo
        dados_tratados["ativo"] = True
        
        return supabase.table("produto").insert(dados_tratados).execute()

    @staticmethod
    def editar(id_prod, dados):
        # Trata o dicionário dinamicamente para manter a padronização na edição
        dados_tratados = {
            chave: valor.strip().upper() if isinstance(valor, str) else valor 
            for chave, valor in dados.items()
        }
        
        # Executa a atualização filtrando pelo ID do produto
        return (
            supabase.table("produto")
            .update(dados_tratados)
            .eq("id", id_prod)
            .execute()
        )

    @staticmethod
    def alternar_status(id_prod):
        # 1. Recupera o estado atual da flag 'ativo'
        busca = supabase.table("produto").select("ativo").eq("id", id_prod).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o valor booleano (True vira False e vice-versa)
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco com o status invertido
            return (
                supabase.table("produto")
                .update({"ativo": novo_status})
                .eq("id", id_prod)
                .execute()
            )
        return busca