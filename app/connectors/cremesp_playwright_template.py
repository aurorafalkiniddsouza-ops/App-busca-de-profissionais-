from __future__ import annotations

from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.connectors.base import BaseCouncilConnector
from app.infra.logger import get_logger


logger = get_logger()


class CremespPlaywrightTemplateConnector(BaseCouncilConnector):
    council_name = "CREMESP"
    search_url = "https://guiamedico.cremesp.org.br/"

    async def search_by_name(self, full_name: str, state: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        logger.info("Iniciando consulta no %s para %s", self.council_name, full_name)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(self.search_url, wait_until="domcontentloaded", timeout=30000)

                # IMPORTANTE:
                # Revisar os seletores abaixo diretamente no portal antes de usar em produção.
                # Eles são placeholders de uma navegação provável e podem mudar conforme o HTML real.
                name_input_selector = 'input[type="text"]'
                submit_selector = 'button[type="submit"], input[type="submit"]'
                results_container_selector = 'table tbody tr, .resultado-busca, .card-medico'

                await page.fill(name_input_selector, full_name)
                await page.click(submit_selector)
                await page.wait_for_load_state("networkidle", timeout=20000)

                rows = await page.query_selector_all(results_container_selector)

                for row in rows:
                    raw_text = (await row.inner_text()).strip()
                    if not raw_text:
                        continue

                    # Placeholder de parsing textual simples.
                    # Refinar quando o HTML real estiver mapeado no portal.
                    results.append(
                        {
                            "found_name": raw_text.split("\n")[0] if raw_text else None,
                            "registration_number": None,
                            "found_state": state,
                            "profession": "MEDICINA",
                            "status_text": None,
                            "evidence_url": page.url,
                            "evidence_note": "Resultado capturado por template Playwright do CREMESP.",
                            "notes": "Seletores e parsing devem ser refinados conforme o HTML real.",
                        }
                    )

                if not results:
                    logger.info("Nenhum resultado localizado para %s no %s", full_name, self.council_name)

                return results

            except PlaywrightTimeoutError:
                logger.exception("Timeout na consulta %s para %s", self.council_name, full_name)
                raise RuntimeError(f"Timeout na consulta do conselho {self.council_name}")
            except Exception:
                logger.exception("Falha na consulta %s para %s", self.council_name, full_name)
                raise
            finally:
                await browser.close()

    def parse_result(
        self,
        raw_item: dict[str, Any],
        searched_name: str,
        searched_state: str | None = None,
    ) -> dict[str, Any]:
        return {
            "found_name": raw_item.get("found_name"),
            "registration_number": raw_item.get("registration_number"),
            "found_state": raw_item.get("found_state", searched_state),
            "profession": raw_item.get("profession", "MEDICINA"),
            "status_text": raw_item.get("status_text"),
            "evidence_url": raw_item.get("evidence_url"),
            "evidence_note": raw_item.get("evidence_note"),
            "notes": raw_item.get("notes"),
        }
