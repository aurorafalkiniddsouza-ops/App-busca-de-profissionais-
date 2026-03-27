from __future__ import annotations

import re
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.connectors.base import BaseCouncilConnector
from app.infra.logger import get_logger


logger = get_logger()


class CremespPlaywrightTemplateV3Connector(BaseCouncilConnector):
    council_name = "CREMESP"
    search_url = "https://guiamedico.cremesp.org.br/"

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
        raise RuntimeError("Nenhum campo de busca visível/enabled foi localizado no CREMESP")

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

    def _parse_raw_text(self, raw_text: str, state: str | None) -> dict[str, Any]:
        normalized = raw_text.replace("\r", "\n").strip()
        parts = [part.strip() for part in re.split(r"\t+|\n+", normalized) if part.strip()]

        found_name = None
        status_text = None
        registration_number = None

        for part in parts:
            upper_part = part.upper()
            if status_text is None and any(token in upper_part for token in ["ATIVO", "ATIVA", "INATIVO", "INATIVA", "SUSPENS", "CANCEL", "IRREGULAR", "REGULAR"]):
                status_text = part
                continue
            if registration_number is None and re.fullmatch(r"\d{4,}", part):
                registration_number = part
                continue
            if found_name is None:
                found_name = part

        if found_name is None and parts:
            found_name = parts[0]

        return {
            "found_name": found_name,
            "registration_number": registration_number,
            "found_state": state,
            "profession": "MEDICINA",
            "status_text": status_text,
        }

    async def search_by_name(self, full_name: str, state: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        logger.info("Iniciando consulta no %s para %s", self.council_name, full_name)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False, slow_mo=400)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})

            try:
                await page.goto(self.search_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)

                name_input_selectors = [
                    'input[name*="nome" i]',
                    'input[id*="nome" i]',
                    'input[placeholder*="nome" i]',
                    'input[type="search"]',
                    'input[type="text"]',
                ]
                submit_selectors = [
                    'button:has-text("Pesquisar")',
                    'button:has-text("Buscar")',
                    'button:has-text("Consultar")',
                    'input[value*="Pesquisar" i]',
                    'input[value*="Buscar" i]',
                    'button[type="submit"]',
                    'input[type="submit"]',
                ]
                results_container_selectors = [
                    'table tbody tr',
                    '.resultado-busca',
                    '.card-medico',
                    '.list-group-item',
                    '.card',
                    'article',
                    '.row',
                ]

                used_input_selector = await self._fill_first_visible(page, name_input_selectors, full_name)
                logger.info("Campo usado no CREMESP: %s", used_input_selector)

                used_submit_selector = await self._click_first_visible(page, submit_selectors)
                if used_submit_selector:
                    logger.info("Botão usado no CREMESP: %s", used_submit_selector)
                else:
                    logger.info("Nenhum botão localizado no CREMESP; usando Enter")
                    await page.keyboard.press("Enter")

                await page.wait_for_timeout(3000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                html = await page.content()
                await page.screenshot(path="cremesp_debug_v3.png", full_page=True)
                with open("cremesp_debug_v3.html", "w", encoding="utf-8") as f:
                    f.write(html)

                candidate_rows = []
                for selector in results_container_selectors:
                    rows = await page.query_selector_all(selector)
                    if rows:
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

                    parsed = self._parse_raw_text(raw_text, state)
                    parsed["evidence_url"] = page.url
                    parsed["evidence_note"] = "Resultado capturado por template Playwright V3 do CREMESP."
                    parsed["notes"] = "Conector em modo de homologação com parsing estruturado para nome, status e CRM."
                    results.append(parsed)

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
