import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = PROJECT_ROOT / "scripts" / "run_production_candidate_single_search_to_file.py"


def _run_single_search(council: str, searched_name: str) -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_file:
        output_path = Path(temp_file.name)

    command = [sys.executable, str(RUNNER_PATH), council, searched_name, str(output_path)]
    completed = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    try:
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
                "notes": stderr or stdout or f"Falha ao executar runner em subprocesso. Exit code: {completed.returncode}",
            }

        if not output_path.exists():
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
                "notes": "Runner não gerou arquivo de saída.",
            }

        raw_json = output_path.read_text(encoding="utf-8").strip()
        if not raw_json:
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
                "notes": "Arquivo de saída do runner veio vazio.",
            }

        return json.loads(raw_json)
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
            "notes": "Arquivo JSON do runner veio inválido.",
        }
    finally:
        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            pass


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
