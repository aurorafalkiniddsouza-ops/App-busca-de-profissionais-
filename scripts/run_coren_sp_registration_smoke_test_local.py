import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.connectors.coren_sp_registration_playwright_template import CorenSPRegistrationPlaywrightTemplateConnector


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Uso: python scripts/run_coren_sp_registration_smoke_test_local.py "NUMERO_DE_INSCRICAO"')

    registration_number = sys.argv[1]
    connector = CorenSPRegistrationPlaywrightTemplateConnector()
    results = await connector.search_by_registration(registration_number, state="SP")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
