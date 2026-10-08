from database.connection import get_supabase

supabase = get_supabase()


class CondicaoPagamentoService:

    @staticmethod
    def listar_todas(apenas_ativos=True):
        """Lista todas as condições de pagamento ativas da tabela 'condicao_pagamento'."""
        query = supabase.table("condicao_pagamento").select("*")

        if apenas_ativos:
            query = query.eq("ativo", True)

        return query.order("condicao_pagamento").execute().data

    @staticmethod
    def criar(
        condicao_pagamento,
        numero_parcelas=1,
        dias=0,
        percentual_juros=0.0,
        percentual_multa=0.0,
        percentual_desconto=0.0,
    ):
        """Cria uma nova condição de pagamento."""
        return (
            supabase.table("condicao_pagamento")
            .insert({
                "condicao_pagamento": condicao_pagamento.strip().upper(),
                "numero_parcelas": numero_parcelas,
                "dias": dias,
                "percentual_juros": percentual_juros,
                "percentual_multa": percentual_multa,
                "percentual_desconto": percentual_desconto,
                "ativo": True,
            })
            .execute()
        )

    @staticmethod
    def editar(
        id_condicao,
        condicao_pagamento,
        numero_parcelas=1,
        dias=0,
        percentual_juros=0.0,
        percentual_multa=0.0,
        percentual_desconto=0.0,
    ):
        """Edita uma condição de pagamento existente."""
        data = {
            "condicao_pagamento": condicao_pagamento.strip().upper(),
            "numero_parcelas": numero_parcelas,
            "dias": dias,
            "percentual_juros": percentual_juros,
            "percentual_multa": percentual_multa,
            "percentual_desconto": percentual_desconto,
        }
        return (
            supabase.table("condicao_pagamento")
            .update(data)
            .eq("id", id_condicao)
            .execute()
        )

    @staticmethod
    def alternar_status(id_condicao):
        """Inverte o status ativo/inativo da condição de pagamento."""
        busca = (
            supabase.table("condicao_pagamento")
            .select("ativo")
            .eq("id", id_condicao)
            .execute()
        )

        if busca.data:
            status_atual = busca.data[0]["ativo"]
            novo_status = not status_atual

            return (
                supabase.table("condicao_pagamento")
                .update({"ativo": novo_status})
                .eq("id", id_condicao)
                .execute()
            )
        return busca