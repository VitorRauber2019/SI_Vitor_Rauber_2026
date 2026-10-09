import os
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from supabase import Client, create_client

# Carrega as variáveis do arquivo .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase_client: Client = create_client(url, key) if url and key else None


class TransportadoraService:
    """Serviço responsável por gerenciar as operações de CRUD e consultas
    da tabela 'transportadoras' no Supabase.
    """

    TABELA = "transportadoras"

    def __init__(self, client: Optional[Client] = None):
        # Permite passar um cliente existente ou utiliza a instância padrão
        self.supabase = client if client else supabase_client

    def criar(self, dados: Dict[str, Any]) -> Tuple[bool, Any]:
        """Cadastra uma nova transportadora na tabela 'transportadoras'."""
        try:
            response = self.supabase.table(self.TABELA).insert(dados).execute()
            if response.data:
                return True, response.data[0]
            return False, "Nenhum dado retornado após a inserção."
        except Exception as e:
            return False, f"Erro ao cadastrar transportadora: {str(e)}"

    def listar_todos(
        self, busca: Optional[str] = None, apenas_ativos: bool = True
    ) -> List[Dict[str, Any]]:
        """Lista as transportadoras cadastradas, permitindo busca por texto e filtro de status."""
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
            print(f"Erro ao listar transportadoras: {str(e)}")
            return []

    def obter_por_id(self, transportadora_id: str) -> Optional[Dict[str, Any]]:
        """Obtém uma transportadora específica pelo seu ID."""
        try:
            response = (
                self.supabase.table(self.TABELA)
                .select("*")
                .eq("id", transportadora_id)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Erro ao obter transportadora {transportadora_id}: {str(e)}")
            return None

    def editar(
        self, transportadora_id: str, dados: Dict[str, Any]
    ) -> Tuple[bool, Any]:
        """Atualiza as informações de uma transportadora existente."""
        try:
            response = (
                self.supabase.table(self.TABELA)
                .update(dados)
                .eq("id", transportadora_id)
                .execute()
            )
            if response.data:
                return True, response.data[0]
            return False, "Transportadora não encontrada ou nenhum dado alterado."
        except Exception as e:
            return False, f"Erro ao atualizar transportadora: {str(e)}"

    def alternar_status(
        self, transportadora_id: str, novo_status: bool
    ) -> Tuple[bool, Any]:
        """Ativa ou inativa o cadastro de uma transportadora (Soft Delete)."""
        return self.editar(transportadora_id, {"status": novo_status})

    def excluir(self, transportadora_id: str) -> Tuple[bool, Any]:
        """Remove permanentemente uma transportadora do banco de dados."""
        try:
            self.supabase.table(self.TABELA).delete().eq(
                "id", transportadora_id
            ).execute()
            return True, "Transportadora removida com sucesso."
        except Exception as e:
            return False, f"Erro ao excluir transportadora: {str(e)}"