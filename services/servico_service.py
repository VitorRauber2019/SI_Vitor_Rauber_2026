from database.connection import get_supabase

supabase = get_supabase()

class ServicoService:
    @staticmethod
    def listar_todos(apenas_ativos=True):
        # Inicia a consulta na tabela servico
        query = supabase.table("servico").select("*")
        
        # Filtra apenas por serviços ativos caso o parâmetro seja True
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        return query.order("nome").execute().data

    @staticmethod
    def criar(nome, preco, duracao):
        # Cadastra o serviço formatando o nome e definindo como ativo por padrão
        return supabase.table("servico").insert({
            "nome": nome.strip().upper(),
            "preco": preco,
            "duracao_minutos": duracao,
            "ativo": True
        }).execute()

    @staticmethod
    def editar(id_servico, nome, preco, duracao):
        # Atualiza os dados do serviço mantendo a padronização do nome
        data = {
            "nome": nome.strip().upper(),
            "preco": preco,
            "duracao_minutos": duracao
        }
        return (
            supabase.table("servico")
            .update(data)
            .eq("id", id_servico)
            .execute()
        )

    @staticmethod
    def alternar_status(id_servico):
        # 1. Recupera o estado atual da flag 'ativo'
        busca = supabase.table("servico").select("ativo").eq("id", id_servico).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o valor booleano (True vira False e vice-versa)
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco com o status invertido
            return (
                supabase.table("servico")
                .update({"ativo": novo_status})
                .eq("id", id_servico)
                .execute()
            )
        return busca