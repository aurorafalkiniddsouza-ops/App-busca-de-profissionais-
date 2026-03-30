import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.connectors.coren_sp_playwright_template_v2 import CorenSPPlaywrightTemplateV2Connector


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Uso: python scripts/run_coren_sp_smoke_test_local_v2.py "NOME DO PROFISSIONAL"')

    searched_name = sys.argv[1]
    connector = CorenSPPlaywrightTemplateV2Connector()
    results = await connector.search_by_name(searched_name, state="SP")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
