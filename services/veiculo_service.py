import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from supabase import Client, create_client

# Carrega as variáveis do arquivo .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase_client: Client = create_client(url, key) if url and key else None


class VeiculoService:
    """Serviço responsável por gerenciar as operações de CRUD e consultas
    da tabela 'veiculos' no Supabase.
    """

    TABELA = "veiculos"
    SELECT = "*, transportadora:transportadoras(razao_social)"

    def __init__(self, client: Optional[Client] = None):
        # Permite passar um cliente existente ou utiliza a instância padrão
        self.supabase = client if client else supabase_client

    def criar(self, dados: Dict[str, Any]) -> Tuple[bool, Any]:
        """Cadastra um novo veículo na tabela 'veiculos'."""
        try:
            response = self.supabase.table(self.TABELA).insert(dados).execute()
            if response.data:
                return True, response.data[0]
            return False, "Nenhum dado retornado após a inserção."
        except Exception as e:
            if "duplicate key" in str(e) or "23505" in str(e):
                return False, "Já existe um veículo cadastrado com esta placa."
            return False, f"Erro ao cadastrar veículo: {str(e)}"

    def listar_todos(
        self, busca: Optional[str] = None, apenas_ativos: bool = True
    ) -> List[Dict[str, Any]]:
        """Lista os veículos cadastrados, permitindo busca por texto e filtro de status."""
        try:
            query = self.supabase.table(self.TABELA).select(self.SELECT)

            if apenas_ativos:
                query = query.eq("ativo", True)

            if busca:
                # Busca por Placa, Modelo ou Marca
                query = query.or_(
                    f"placa.ilike.%{busca}%,modelo.ilike.%{busca}%,marca.ilike.%{busca}%"
                )

            response = query.order("placa", desc=False).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao listar veículos: {str(e)}")
            return []

    def listar_por_transportadora(self, transportadora_id: int) -> List[Dict[str, Any]]:
        """Lista os veículos vinculados a uma transportadora."""
        try:
            response = (
                self.supabase.table(self.TABELA)
                .select(self.SELECT)
                .eq("transportadora_id", transportadora_id)
                .order("placa", desc=False)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao listar veículos da transportadora {transportadora_id}: {str(e)}")
            return []

    def obter_por_id(self, veiculo_id: int) -> Optional[Dict[str, Any]]:
        """Obtém um veículo específico pelo seu ID."""
        try:
            response = (
                self.supabase.table(self.TABELA)
                .select(self.SELECT)
                .eq("id", veiculo_id)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"Erro ao obter veículo {veiculo_id}: {str(e)}")
            return None

    def editar(self, veiculo_id: int, dados: Dict[str, Any]) -> Tuple[bool, Any]:
        """Atualiza as informações de um veículo existente."""
        try:
            dados = {**dados, "updated_at": datetime.now(timezone.utc).isoformat()}
            response = (
                self.supabase.table(self.TABELA)
                .update(dados)
                .eq("id", veiculo_id)
                .execute()
            )
            if response.data:
                return True, response.data[0]
            return False, "Veículo não encontrado ou nenhum dado alterado."
        except Exception as e:
            if "duplicate key" in str(e) or "23505" in str(e):
                return False, "Já existe um veículo cadastrado com esta placa."
            return False, f"Erro ao atualizar veículo: {str(e)}"

    def alternar_status(self, veiculo_id: int, novo_status: bool) -> Tuple[bool, Any]:
        """Ativa ou inativa o cadastro de um veículo (Soft Delete)."""
        return self.editar(veiculo_id, {"ativo": novo_status})

    def sincronizar_transportadora(
        self, transportadora_id: int, veiculo_ids: List[int]
    ) -> Tuple[bool, Any]:
        """Vincula os veículos informados à transportadora e desvincula os que saíram da lista."""
        try:
            ids = [int(i) for i in veiculo_ids if i is not None]

            desvincular = self.supabase.table(self.TABELA).update(
                {"transportadora_id": None}
            ).eq("transportadora_id", transportadora_id)
            if ids:
                desvincular = desvincular.not_.in_("id", ids)
            desvincular.execute()

            if ids:
                self.supabase.table(self.TABELA).update(
                    {"transportadora_id": transportadora_id}
                ).in_("id", ids).execute()
            return True, "Veículos vinculados com sucesso."
        except Exception as e:
            return False, f"Erro ao vincular veículos: {str(e)}"
