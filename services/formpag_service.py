from database.connection import get_supabase

supabase = get_supabase()

class FormaPagamentoService:
    @staticmethod
    def listar_todas(apenas_ativos=True):
        # Inicia a consulta na tabela forma_pagamento
        query = supabase.table("forma_pagamento").select("*")
        
        # Filtra apenas pelas ativas caso o parâmetro seja True
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        return query.order("forma_pagamento").execute().data

    @staticmethod
    def criar(nome, descricao):
        return supabase.table("forma_pagamento").insert({
            "forma_pagamento": nome.strip().upper(),
            "descricao": descricao.strip().upper(),
            "ativo": True
        }).execute()

    @staticmethod
    def editar(id_forma, nome, descricao):
        # Atualiza os campos aplicando a formatação padrão
        data = {
            "forma_pagamento": nome.strip().upper(),
            "descricao": descricao.strip().upper()
        }
        return (
            supabase.table("forma_pagamento")
            .update(data)
            .eq("id", id_forma)
            .execute()
        )

    @staticmethod
    def alternar_status(id_forma):
        # 1. Recupera o estado atual da flag 'ativo'
        busca = supabase.table("forma_pagamento").select("ativo").eq("id", id_forma).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o valor booleano (True vira False e vice-versa)
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco com o status invertido
            return (
                supabase.table("forma_pagamento")
                .update({"ativo": novo_status})
                .eq("id", id_forma)
                .execute()
            )
        return busca