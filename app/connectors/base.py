from abc import ABC, abstractmethod
from typing import Any


class BaseCouncilConnector(ABC):
    council_name: str

    @abstractmethod
    async def search_by_name(self, full_name: str, state: str | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def parse_result(
        self,
        raw_item: dict[str, Any],
        searched_name: str,
        searched_state: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError
