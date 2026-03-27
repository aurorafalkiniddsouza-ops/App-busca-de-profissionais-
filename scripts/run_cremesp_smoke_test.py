import asyncio
import json
import sys

from app.connectors.cremesp_playwright_template import CremespPlaywrightTemplateConnector


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python scripts/run_cremesp_smoke_test.py \"NOME DO PROFISSIONAL\"")

    searched_name = sys.argv[1]
    connector = CremespPlaywrightTemplateConnector()
    results = await connector.search_by_name(searched_name, state="SP")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
