import asyncio
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.exporter import dataframe_to_excel_bytes
from app.services.search_service_production_candidate import process_dataframe


async def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit('Uso: python scripts/run_production_candidate_excel.py "CONSELHO" "CAMINHO_DO_ARQUIVO.xlsx"')

    council = sys.argv[1]
    input_path = Path(sys.argv[2])
    if not input_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {input_path}")

    dataframe = pd.read_excel(input_path)
    result_dataframe = await process_dataframe(dataframe=dataframe, council=council, searched_state="SP")

    output_path = input_path.with_name(f"resultado_{input_path.stem}.xlsx")
    output_path.write_bytes(dataframe_to_excel_bytes(result_dataframe))
    print(f"Arquivo gerado com sucesso: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
