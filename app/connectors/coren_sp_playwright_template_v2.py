from __future__ import annotations

from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.connectors.base import BaseCouncilConnector
from app.infra.logger import get_logger


logger = get_logger()


class CorenSPPlaywrightTemplateV2Connector(BaseCouncilConnector):
    council_name = "COREN-SP"
    search_url = "https://servicos.coren-sp.gov.br/consulta-de-profissionais/"

    async def _fill_first_visible(self, page, selectors: list[str], value: str) -> str:
        for selector in selectors:
            locator = page.locator(selector)
            count = await locator.count()
            if count == 0:
                continue
            for index in range(count):
                element = locator.nth(index)
                try:
                    if await element.is_visible() and await element.is_enabled():
                        await element.fill(value)
                        return selector
                except Exception:
                    continue
        raise RuntimeError("Campo de nome não localizado no portal COREN-SP")

    async def _click_first_visible(self, page, selectors: list[str]) -> str | None:
        for selector in selectors:
            locator = page.locator(selector)
            count = await locator.count()
            if count == 0:
                continue
            for index in range(count):
                element = locator.nth(index)
                try:
                    if await element.is_visible() and await element.is_enabled():
                        await element.click()
                        return selector
                except Exception:
                    continue
        return None

    async def search_by_name(self, full_name: str, state: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        logger.info("Iniciando consulta no %s para %s", self.council_name, full_name)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False, slow_mo=400)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})

            try:
                await page.goto(self.search_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2500)

                print("URL inicial:", page.url)
                print("Título inicial:", await page.title())

                name_input_selectors = [
                    'input[name*="nome" i]',
                    'input[id*="nome" i]',
                    'input[placeholder*="nome" i]',
                    'input[aria-label*="nome" i]',
                    'input[type="search"]',
                    'input[type="text"]',
                    'textarea',
                ]
                submit_selectors = [
                    'button:has-text("Consultar")',
                    'button:has-text("Pesquisar")',
                    'button:has-text("Buscar")',
                    'button:has-text("Procurar")',
                    'input[value*="Consultar" i]',
                    'input[value*="Pesquisar" i]',
                    'input[value*="Buscar" i]',
                    'button[type="submit"]',
                    'input[type="submit"]',
                ]
                results_container_selectors = [
                    'table tbody tr',
                    '.resultado',
                    '.resultado-busca',
                    '.card',
                    '.card-body',
                    '.list-group-item',
                    '.row',
                    'article',
                ]

                used_input_selector = await self._fill_first_visible(page, name_input_selectors, full_name)
                print("Campo usado:", used_input_selector)
                print("Nome preenchido:", full_name)

                used_submit_selector = await self._click_first_visible(page, submit_selectors)
                if used_submit_selector:
                    print("Botão usado:", used_submit_selector)
                else:
                    print("Nenhum botão encontrado. Tentando Enter no campo.")
                    await page.keyboard.press("Enter")

                await page.wait_for_timeout(3000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                print("URL final:", page.url)
                print("Título final:", await page.title())

                html = await page.content()
                print("HTML parcial:")
                print(html[:5000])

                await page.screenshot(path="coren_sp_debug_v2.png", full_page=True)
                with open("coren_sp_debug_v2.html", "w", encoding="utf-8") as f:
                    f.write(html)

                candidate_rows = []
                for selector in results_container_selectors:
                    rows = await page.query_selector_all(selector)
                    if rows:
                        print(f"Seletor de resultado com matches: {selector} -> {len(rows)}")
                        candidate_rows.extend(rows)

                seen_texts = set()
                first_name = full_name.upper().split()[0]
                last_name = full_name.upper().split()[-1]

                for row in candidate_rows:
                    raw_text = (await row.inner_text()).strip()
                    if not raw_text or raw_text in seen_texts:
                        continue
                    seen_texts.add(raw_text)

                    upper_text = raw_text.upper()
                    if first_name not in upper_text and last_name not in upper_text:
                        continue

                    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
                    found_name = lines[0] if lines else None
                    status_text = None
                    registration_number = None

                    for line in lines:
                        upper_line = line.upper()
                        if any(keyword in upper_line for keyword in ["ATIV", "INATIV", "SUSPENS", "CANCEL", "BAIXAD", "REGULAR", "IRREGULAR"]):
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
                            "evidence_note": "Resultado capturado por template Playwright V2 do COREN-SP.",
                            "notes": "Conector em modo de homologação; revisar seletores e parsing conforme HTML real e eventuais proteções.",
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
