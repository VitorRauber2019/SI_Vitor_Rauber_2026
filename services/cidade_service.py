import os
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key) if url and key else None


class CidadeService:

    @classmethod
    def listar_todos(cls, apenas_ativos: bool = True):
        """Lista todas as cidades com os dados aninhados do Estado e do País."""
        if not supabase:
            return []

        # Traz Cidade + Estado + País vinculado ao Estado
        query = supabase.table("cidade").select("*, estado(*, pais(*))")

        if apenas_ativos:
            query = query.eq("ativo", True)

        response = query.order("nome").execute()
        return response.data if response.data else []

    @classmethod
    def criar(cls, nome: str, estado_id: int):
        """Cria uma nova cidade vinculada a um estado."""
        data = {"nome": nome, "estado_id": estado_id, "ativo": True}
        response = supabase.table("cidade").insert(data).execute()
        return response.data[0] if response.data else None

    @classmethod
    def editar(cls, id_cidade: int, nome: str, estado_id: int):
        """Edita o nome ou o estado associado a uma cidade existente."""
        data = {"nome": nome, "estado_id": estado_id}
        response = (
            supabase.table("cidade")
            .update(data)
            .eq("id", id_cidade)
            .execute()
        )
        return response.data[0] if response.data else None

    @classmethod
    def alternar_status(cls, id_cidade: int):
        """Alterna o status de ativo/desativado (Soft Delete)."""
        cidade = (
            supabase.table("cidade")
            .select("ativo")
            .eq("id", id_cidade)
            .single()
            .execute()
        )

        if cidade.data:
            novo_status = not cidade.data.get("ativo", True)
            supabase.table("cidade").update({"ativo": novo_status}).eq(
                "id", id_cidade
            ).execute()