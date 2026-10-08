from typing import Dict, List, Optional, Tuple, Any
from supabase import Client


class FornecedorService:
    """
    Serviço responsável por gerenciar a regra de negócio e as operações
    de banco de dados para a entidade Fornecedores no Supabase.
    """

    TABELA = "fornecedores"

    def __init__(self, client: Client):
        self.supabase = client

    def criar(self, dados: Dict[str, Any]) -> Tuple[bool, Any]:
        """
        Cadastra um novo fornecedor.
        Retorna uma tupla (sucesso: bool, dados_ou_mensagem: Any)
        """
        try:
            response = self.supabase.table(self.TABELA).insert(dados).execute()
            if response.data:
                return True, response.data[0]
            return False, "Nenhum dado foi retornado após a inserção."
        except Exception as e:
            return False, f"Erro ao cadastrar fornecedor: {str(e)}"

    def listar(
        self, busca: Optional[str] = None, apenas_ativos: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Lista fornecedores com suporte a filtro por texto (Razão Social/CNPJ) e status ativo.
        """
        try:
            query = self.supabase.table(self.TABELA).select("*")

            if apenas_ativos:
                query = query.eq("status", True)

            if busca:
                # Busca por Razão Social, Nome Fantasia ou CNPJ/CPF
                query = query.or_(
                    f"razao_social.ilike.%{busca}%,nome_fantasia.ilike.%{busca}%,cnpj_cpf.ilike.%{busca}%"
                )

            response = query.order("razao_social", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao listar fornecedores: {str(e)}")
            return []

    def obter_por_id(self, fornecedor_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca o cadastro completo de um fornecedor pelo seu UUID.
        """
        try:
            response = (
                self.supabase.table(self.TABELA)
                .select("*")
                .eq("id", fornecedor_id)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Erro ao obter fornecedor {fornecedor_id}: {str(e)}")
            return None

    def atualizar(
        self, fornecedor_id: str, dados: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """
        Atualiza as informações de um fornecedor existente pelo ID.
        """
        try:
            response = (
                self.supabase.table(self.TABELA)
                .update(dados)
                .eq("id", fornecedor_id)
                .execute()
            )
            if response.data:
                return True, response.data[0]
            return False, "Fornecedor não encontrado ou nenhum dado alterado."
        except Exception as e:
            return False, f"Erro ao atualizar fornecedor: {str(e)}"

    def alternar_status(
        self, fornecedor_id: str, novo_status: bool
    ) -> Tuple[bool, Any]:
        """
        Ativa ou inativa um fornecedor rapidamente.
        """
        return self.atualizar(fornecedor_id, {"status": novo_status})

    def excluir(self, fornecedor_id: str) -> Tuple[bool, Any]:
        """
        Remove um fornecedor do banco de dados pelo ID.
        """
        try:
            response = (
                self.supabase.table(self.TABELA)
                .delete()
                .eq("id", fornecedor_id)
                .execute()
            )
            return True, "Fornecedor removido com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir fornecedor: {str(e)}"