from typing import Any

from app.connectors.base import BaseCouncilConnector


class CorenSPConnector(BaseCouncilConnector):
    council_name = "COREN-SP"

    async def search_by_name(self, full_name: str, state: str | None = None) -> list[dict[str, Any]]:
        """
        Scaffold inicial.
        Substituir por automação real com Playwright após validação do fluxo no portal.
        """
        return []

    def parse_result(
        self,
        raw_item: dict[str, Any],
        searched_name: str,
        searched_state: str | None = None,
    ) -> dict[str, Any]:
        return {
            "found_name": raw_item.get("found_name"),
            "registration_number": raw_item.get("registration_number"),
            "found_state": raw_item.get("found_state", searched_state),
            "profession": raw_item.get("profession", "ENFERMAGEM"),
            "status_text": raw_item.get("status_text"),
            "evidence_url": raw_item.get("evidence_url"),
            "evidence_note": raw_item.get("evidence_note", "Consulta inicial COREN-SP"),
            "notes": raw_item.get("notes"),
        }
