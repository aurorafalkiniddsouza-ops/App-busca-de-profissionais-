import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.connectors.cremesp_playwright_template_v3 import CremespPlaywrightTemplateV3Connector


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Uso: python scripts/run_cremesp_smoke_test_local_v3.py "NOME DO PROFISSIONAL"')

    searched_name = sys.argv[1]
    connector = CremespPlaywrightTemplateV3Connector()
    results = await connector.search_by_name(searched_name, state="SP")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
