import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.search_service_production_candidate import process_single_search


async def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit('Uso: python scripts/run_production_candidate_single_search_to_file.py "CONSELHO" "NOME DO PROFISSIONAL" "ARQUIVO_SAIDA.json"')

    council = sys.argv[1]
    searched_name = sys.argv[2]
    output_path = Path(sys.argv[3])

    result = await process_single_search(
        searched_name=searched_name,
        council=council,
        searched_state="SP",
    )

    output_path.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(main())
