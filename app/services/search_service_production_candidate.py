from datetime import datetime

import pandas as pd

from app.connectors.registry_production_candidate import get_connector
from app.core.classifier import classify_status
from app.core.matcher import name_similarity
from app.core.models import SearchResult


async def process_single_search(
    searched_name: str,
    council: str,
    searched_state: str | None = None,
) -> SearchResult:
    connector = get_connector(council)

    try:
        raw_results = await connector.search_by_name(searched_name, searched_state)

        if not raw_results:
            return SearchResult(
                searched_name=searched_name,
                council=council,
                searched_state=searched_state,
                final_status="NÃO ENCONTRADO",
                confidence_score=0.0,
                queried_at=datetime.now(),
                notes="Nenhum resultado retornado pelo conector.",
            )

        parsed_results = [
            connector.parse_result(raw_item, searched_name, searched_state)
            for raw_item in raw_results
        ]

        for item in parsed_results:
            item["confidence_score"] = name_similarity(
                searched_name,
                item.get("found_name", ""),
            )

        parsed_results.sort(key=lambda item: item["confidence_score"], reverse=True)

        if len(parsed_results) > 1:
            difference = parsed_results[0]["confidence_score"] - parsed_results[1]["confidence_score"]
            if difference < 5:
                return SearchResult(
                    searched_name=searched_name,
                    council=council,
                    searched_state=searched_state,
                    final_status="MÚLTIPLOS RESULTADOS",
                    confidence_score=parsed_results[0]["confidence_score"],
                    queried_at=datetime.now(),
                    notes="Mais de um resultado com score semelhante.",
                )

        best_result = parsed_results[0]
        final_status = classify_status(best_result.get("status_text"))

        return SearchResult(
            searched_name=searched_name,
            council=council,
            searched_state=searched_state,
            found_name=best_result.get("found_name"),
            registration_number=best_result.get("registration_number"),
            found_state=best_result.get("found_state"),
            profession=best_result.get("profession"),
            status_text=best_result.get("status_text"),
            final_status=final_status,
            confidence_score=best_result.get("confidence_score", 0.0),
            evidence_url=best_result.get("evidence_url"),
            evidence_note=best_result.get("evidence_note"),
            queried_at=datetime.now(),
            notes=best_result.get("notes"),
        )

    except Exception as exc:
        return SearchResult(
            searched_name=searched_name,
            council=council,
            searched_state=searched_state,
            final_status="ERRO NA CONSULTA",
            confidence_score=0.0,
            queried_at=datetime.now(),
            notes=str(exc),
        )


async def process_dataframe(dataframe: pd.DataFrame, council: str, searched_state: str | None = None) -> pd.DataFrame:
    results = []

    for _, row in dataframe.iterrows():
        searched_name = str(row.get("nome", "")).strip()
        if not searched_name:
            continue

        result = await process_single_search(searched_name, council, searched_state)
        results.append(result.model_dump())

    return pd.DataFrame(results)
