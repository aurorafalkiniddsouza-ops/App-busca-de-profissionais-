from __future__ import annotations

from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.connectors.base import BaseCouncilConnector
from app.infra.logger import get_logger


logger = get_logger()


class CorenSPPlaywrightTemplateConnector(BaseCouncilConnector):
    council_name = "COREN-SP"
    search_url = "https://servicos.coren-sp.gov.br/consulta-de-profissionais/"

    async def search_by_name(self, full_name: str, state: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        logger.info("Iniciando consulta no %s para %s", self.council_name, full_name)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(self.search_url, wait_until="domcontentloaded", timeout=30000)

                # IMPORTANTE:
                # Este portal pode apresentar mecanismos de proteção adicionais.
                # Os seletores abaixo são placeholders de uma navegação provável.
                # Revisar o HTML real antes de uso em produção.
                name_input_selectors = [
                    'input[name="nome"]',
                    'input[placeholder*="Nome"]',
                    'input[type="text"]',
                ]
                submit_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:has-text("Consultar")',
                    'button:has-text("Pesquisar")',
                ]
                results_container_selector = 'table tbody tr, .resultado, .resultado-busca, .card, .list-group-item'

                input_filled = False
                for selector in name_input_selectors:
                    locator = page.locator(selector)
                    if await locator.count() > 0:
                        await locator.first.fill(full_name)
                        input_filled = True
                        break

                if not input_filled:
                    raise RuntimeError("Campo de nome não localizado no portal COREN-SP")

                submitted = False
                for selector in submit_selectors:
                    locator = page.locator(selector)
                    if await locator.count() > 0:
                        await locator.first.click()
                        submitted = True
                        break

                if not submitted:
                    raise RuntimeError("Botão de consulta não localizado no portal COREN-SP")

                await page.wait_for_load_state("networkidle", timeout=20000)

                rows = await page.query_selector_all(results_container_selector)

                for row in rows:
                    raw_text = (await row.inner_text()).strip()
                    if not raw_text:
                        continue

                    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
                    found_name = lines[0] if lines else None
                    status_text = None
                    registration_number = None

                    for line in lines:
                        upper_line = line.upper()
                        if any(keyword in upper_line for keyword in ["ATIV", "INATIV", "SUSPENS", "CANCEL", "BAIXAD"]):
                            status_text = line
                        if any(keyword in upper_line for keyword in ["INSCRI", "REGIST", "COREN"]):
                            registration_number = line

                    results.append(
                        {
                            "found_name": found_name,
                            "registration_number": registration_number,
                            "found_state": state or "SP",
                            "profession": "ENFERMAGEM",
                            "status_text": status_text,
                            "evidence_url": page.url,
                            "evidence_note": "Resultado capturado por template Playwright do COREN-SP.",
                            "notes": "Seletores e parsing devem ser refinados conforme o HTML real e eventuais proteções do portal.",
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
            "found_state": raw_item.get("found_state", searched_state or "SP"),
            "profession": raw_item.get("profession", "ENFERMAGEM"),
            "status_text": raw_item.get("status_text"),
            "evidence_url": raw_item.get("evidence_url"),
            "evidence_note": raw_item.get("evidence_note"),
            "notes": raw_item.get("notes"),
        }
