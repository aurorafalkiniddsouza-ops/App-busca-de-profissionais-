import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_production_candidate_single_search.py"


def _run_single_search(council: str, searched_name: str) -> dict:
    command = [sys.executable, str(RUNNER_PATH), council, searched_name]
    completed = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    if completed.returncode != 0:
        return {
            "searched_name": searched_name,
            "council": council,
            "searched_state": "SP",
            "found_name": None,
            "registration_number": None,
            "found_state": None,
            "profession": None,
            "status_text": None,
            "final_status": "ERRO NA CONSULTA",
            "confidence_score": 0.0,
            "evidence_url": None,
            "evidence_note": None,
            "queried_at": None,
            "notes": completed.stderr.strip() or completed.stdout.strip() or "Falha ao executar runner em subprocesso.",
        }

    stdout = completed.stdout.strip()
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {
            "searched_name": searched_name,
            "council": council,
            "searched_state": "SP",
            "found_name": None,
            "registration_number": None,
            "found_state": None,
            "profession": None,
            "status_text": None,
            "final_status": "ERRO NA CONSULTA",
            "confidence_score": 0.0,
            "evidence_url": None,
            "evidence_note": None,
            "queried_at": None,
            "notes": stdout[:1000] or "Runner retornou saída não-JSON.",
        }


def process_dataframe_streamlit_safe(
    dataframe: pd.DataFrame,
    council: str,
    delay_between_rows_seconds: float = 1.5,
) -> pd.DataFrame:
    results = []

    for _, row in dataframe.iterrows():
        searched_name = str(row.get("nome", "")).strip()
        if not searched_name:
            continue

        result = _run_single_search(council=council, searched_name=searched_name)
        results.append(result)
        time.sleep(delay_between_rows_seconds)

    return pd.DataFrame(results)
