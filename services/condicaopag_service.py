from database.connection import get_supabase

supabase = get_supabase()

class CondicaoPagamentoService:
    
    @staticmethod
    def listar_todas(apenas_ativos=True):
        """Lista apenas os cabeçalhos das condições (para a tela de busca)."""
        query = supabase.table("condicao_pagamento").select("*")
        if apenas_ativos:
            query = query.eq("ativo", True)
        return query.order("condicao_pagamento").execute().data

    @staticmethod
    def listar_parcelas(condicao_id):
        """Busca os detalhes (parcelas) de uma condição específica para a tela de edição."""
        return (
            supabase.table("condicao_pagamento_parcelas")
            .select("*")
            .eq("condicao_pagamento_id", condicao_id)
            .order("numero_parcela")
            .execute()
            .data
        )

    @staticmethod
    def existe_nome(nome, ignorar_id=None):
        """Verifica se já existe uma condição com o mesmo nome (ignorando maiúsculas/minúsculas)."""
        query = (
            supabase.table("condicao_pagamento")
            .select("id")
            .ilike("condicao_pagamento", nome.strip())
        )
        if ignorar_id:
            query = query.neq("id", ignorar_id)
        return bool(query.execute().data)

    @staticmethod
    def criar_com_parcelas(dados_cabecalho, parcelas):
        """Insere o cabeçalho e as parcelas filhas."""
        try:
            if CondicaoPagamentoService.existe_nome(dados_cabecalho["condicao_pagamento"]):
                return False, "Já existe uma condição de pagamento com esse nome."

            # 1. Insere o Cabeçalho
            res_cab = supabase.table("condicao_pagamento").insert(dados_cabecalho).execute()
            
            if res_cab.data:
                condicao_id = res_cab.data[0]["id"]
                
                # 2. Associa o ID do cabeçalho recém-criado a todas as parcelas
                for p in parcelas:
                    p["condicao_pagamento_id"] = condicao_id
                    
                # 3. Insere as Parcelas (se houver)
                if parcelas:
                    supabase.table("condicao_pagamento_parcelas").insert(parcelas).execute()
                    
                return True, res_cab.data[0]
            
            return False, "Erro ao criar cabeçalho da Condição."
        except Exception as e:
            if "23505" in str(e):
                return False, "Já existe uma condição de pagamento com esse nome."
            return False, str(e)

    @staticmethod
    def editar_com_parcelas(id_condicao, dados_cabecalho, parcelas):
        """Atualiza o cabeçalho, deleta as parcelas antigas e insere as novas."""
        try:
            if CondicaoPagamentoService.existe_nome(dados_cabecalho["condicao_pagamento"], ignorar_id=id_condicao):
                return False, "Já existe uma condição de pagamento com esse nome."

            # 1. Atualiza o Cabeçalho
            supabase.table("condicao_pagamento").update(dados_cabecalho).eq("id", id_condicao).execute()
            
            # 2. Exclui as parcelas antigas desta condição
            supabase.table("condicao_pagamento_parcelas").delete().eq("condicao_pagamento_id", id_condicao).execute()
            
            # 3. Insere as parcelas atualizadas
            for p in parcelas:
                p["condicao_pagamento_id"] = id_condicao
                
            if parcelas:
                supabase.table("condicao_pagamento_parcelas").insert(parcelas).execute()
                
            return True, "Condição atualizada com sucesso."
        except Exception as e:
            if "23505" in str(e):
                return False, "Já existe uma condição de pagamento com esse nome."
            return False, str(e)

    @staticmethod
    def alternar_status(id_condicao):
        """Ativa ou desativa a condição de pagamento."""
        busca = supabase.table("condicao_pagamento").select("ativo").eq("id", id_condicao).execute()
        if busca.data:
            novo_status = not busca.data[0]["ativo"]
            return (
                supabase.table("condicao_pagamento")
                .update({"ativo": novo_status})
                .eq("id", id_condicao)
                .execute()
            )
        return None