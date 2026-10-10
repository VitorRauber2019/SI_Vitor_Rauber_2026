import os
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from supabase import Client, create_client

# Carrega as variáveis do ficheiro .env
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase_client: Client = create_client(url, key) if url and key else None

# Campos que formam a chave primária composta da compra
CAMPOS_CHAVE = ("modelo", "serie", "numero", "fornecedor_cnpj_cpf")


class CompraService:
    """Serviço responsável pelas compras (tabelas 'compras', 'compras_itens' e 'compras_parcelas').

    A chave da compra é composta por modelo + série + número + CNPJ/CPF do fornecedor.
    Uma compra só pode ser lançada ou cancelada (sem edição): ambas as operações são feitas
    pelas funções SQL 'lancar_compra' e 'cancelar_compra', que também movimentam o estoque.
    """

    TABELA_COMPRAS = "compras"
    TABELA_ITENS = "compras_itens"
    TABELA_PARCELAS = "compras_parcelas"

    def __init__(self, client: Optional[Client] = None):
        self.supabase = client if client else supabase_client

    @staticmethod
    def _mensagem_erro(e: Exception) -> str:
        """Extrai a mensagem amigável de um erro do PostgREST."""
        if e.args and isinstance(e.args[0], dict) and e.args[0].get("message"):
            return e.args[0]["message"]
        return getattr(e, "message", None) or str(e)

    def _filtrar_chave(self, query, chave: Dict[str, Any]):
        for campo in CAMPOS_CHAVE:
            query = query.eq(campo, chave[campo])
        return query

    def lancar(
        self,
        dados_compra: Dict[str, Any],
        itens: List[Dict[str, Any]],
        parcelas: List[Dict[str, Any]],
    ) -> Tuple[bool, Any]:
        """Lança a compra com itens e parcelas e dá entrada no estoque (transação única)."""
        try:
            res = self.supabase.rpc(
                "lancar_compra",
                {"p_compra": dados_compra, "p_itens": itens, "p_parcelas": parcelas},
            ).execute()
            return True, res.data
        except Exception as e:
            return False, self._mensagem_erro(e)

    def cancelar(self, chave: Dict[str, Any], motivo: str) -> Tuple[bool, Any]:
        """Cancela a compra e estorna o estoque dos produtos."""
        try:
            self.supabase.rpc(
                "cancelar_compra",
                {
                    "p_modelo": chave["modelo"],
                    "p_serie": chave["serie"],
                    "p_numero": chave["numero"],
                    "p_fornecedor_cnpj_cpf": chave["fornecedor_cnpj_cpf"],
                    "p_motivo": motivo,
                },
            ).execute()
            return True, "Compra cancelada com sucesso."
        except Exception as e:
            return False, self._mensagem_erro(e)

    def listar_todas(
        self, busca: Optional[str] = None, situacao: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista as compras. situacao: 'LANCADA', 'CANCELADA' ou None (todas)."""
        try:
            query = self.supabase.table(self.TABELA_COMPRAS).select("*")

            if situacao:
                query = query.eq("situacao", situacao)

            if busca:
                query = query.or_(
                    f"numero.ilike.%{busca}%,fornecedor_nome.ilike.%{busca}%,fornecedor_cnpj_cpf.ilike.%{busca}%"
                )

            response = query.order("created_at", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Erro ao listar compras: {str(e)}")
            return []

    def obter(self, chave: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obtém os dados completos de uma compra com itens e parcelas."""
        try:
            compra = self._filtrar_chave(
                self.supabase.table(self.TABELA_COMPRAS).select("*"), chave
            ).execute()
            if not compra.data:
                return None

            itens = self._filtrar_chave(
                self.supabase.table(self.TABELA_ITENS).select("*"), chave
            ).order("id").execute()
            parcelas = self._filtrar_chave(
                self.supabase.table(self.TABELA_PARCELAS).select("*"), chave
            ).order("numero_parcela").execute()

            dados = compra.data[0]
            dados["itens"] = itens.data or []
            dados["parcelas"] = parcelas.data or []
            return dados
        except Exception as e:
            print(f"Erro ao obter compra: {str(e)}")
            return None

    def existe(self, modelo: str, serie: str, numero: str, fornecedor_cnpj_cpf: str) -> bool:
        """Verifica se já existe compra com a mesma chave (modelo + série + número + fornecedor)."""
        chave = {
            "modelo": modelo,
            "serie": serie,
            "numero": numero,
            "fornecedor_cnpj_cpf": fornecedor_cnpj_cpf,
        }
        res = self._filtrar_chave(
            self.supabase.table(self.TABELA_COMPRAS).select("numero"), chave
        ).execute()
        return bool(res.data)
