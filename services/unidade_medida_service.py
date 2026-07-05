from database.connection import get_supabase

supabase = get_supabase()

class UnidadeMedidaService:
    @staticmethod
    def listar_todas(apenas_ativos=True):
        # Inicia a consulta na tabela unidade_medida
        query = supabase.table("unidade_medida").select("*")
        
        # Filtra apenas pelas unidades ativas caso o parâmetro seja True
        if apenas_ativos:
            query = query.eq("ativo", True)
            
        return query.order("unidade_medida").execute().data

    @staticmethod
    def criar(nome, sigla):
        return supabase.table("unidade_medida").insert({
            "unidade_medida": nome.strip().upper(), 
            "sigla": sigla.strip().upper(),
            "ativo": True
        }).execute()

    @staticmethod
    def editar(id_un, nome, sigla):
        # Prepara os dados atualizados aplicando a formatação padrão em caixa alta
        data = {
            "unidade_medida": nome.strip().upper(),
            "sigla": sigla.strip().upper()
        }
        # Executa a atualização filtrando pelo ID da unidade de medida
        return (
            supabase.table("unidade_medida")
            .update(data)
            .eq("id", id_un)
            .execute()
        )

    @staticmethod
    def alternar_status(id_un):
        # 1. Recupera o estado atual da flag 'ativo'
        busca = supabase.table("unidade_medida").select("ativo").eq("id", id_un).execute()
        
        if busca.data:
            status_atual = busca.data[0]["ativo"]
            
            # 2. Inverte o valor booleano (True vira False e vice-versa)
            novo_status = not status_atual
            
            # 3. Atualiza o registro no banco com o status invertido
            return (
                supabase.table("unidade_medida")
                .update({"ativo": novo_status})
                .eq("id", id_un)
                .execute()
            )
        return busca