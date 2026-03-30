from __future__ import annotations

import re
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.connectors.base import BaseCouncilConnector
from app.infra.logger import get_logger


logger = get_logger()


class CorenSPRegistrationPlaywrightTemplateV3Connector(BaseCouncilConnector):
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
        raise RuntimeError("Campo de número de inscrição não localizado no portal COREN-SP")

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

    async def _select_registration_criterion(self, page) -> bool:
        criterion_selectors = [
            'label:has-text("Número da inscrição")',
            'label:has-text("Numero da inscricao")',
            'text="Número da inscrição"',
            'text="Numero da inscricao"',
            'input[type="radio"][value*="inscr" i]',
            'input[type="radio"][id*="inscr" i]',
            'input[type="radio"][name*="criterio" i]',
            'select',
        ]

        for selector in criterion_selectors:
            locator = page.locator(selector)
            count = await locator.count()
            if count == 0:
                continue

            for index in range(count):
                element = locator.nth(index)
                try:
                    if not await element.is_visible():
                        continue

                    tag_name = await element.evaluate("(el) => el.tagName.toLowerCase()")

                    if tag_name == "label":
                        await element.click()
                        print("Critério selecionado via label:", selector)
                        return True

                    if tag_name == "input":
                        input_type = await element.get_attribute("type")
                        if input_type in ["radio", "checkbox"]:
                            await element.check()
                            print("Critério selecionado via input:", selector)
                            return True

                    if tag_name == "select":
                        options = await element.locator("option").all_inner_texts()
                        for option_text in options:
                            if "inscri" in option_text.lower():
                                await element.select_option(label=option_text)
                                print("Critério selecionado via select:", option_text)
                                return True
                except Exception:
                    continue

        print("Critério por inscrição selecionado:", False)
        return False

    def _is_form_header_noise(self, raw_text: str) -> bool:
        upper = raw_text.upper()
        noise_patterns = [
            "CRITÉRIO PARA PESQUISA",
            "CRITERIO PARA PESQUISA",
            "NÚMERO DA INSCRIÇÃO",
            "NUMERO DA INSCRICAO",
            "NOME",
            "PESQUISAR",
            "CONSULTAR",
        ]
        return any(pattern in upper for pattern in noise_patterns) and len(raw_text.splitlines()) <= 6

    def _parse_result_block(self, raw_text: str, registration_number: str, state: str | None) -> dict[str, Any]:
        normalized = raw_text.replace("\r", "\n").strip()
        parts = [part.strip() for part in re.split(r"\t+|\n+", normalized) if part.strip()]

        found_name = None
        status_text = None
        parsed_registration_number = None

        for part in parts:
            upper = part.upper()
            if found_name is None and not any(token in upper for token in ["ATIVO", "ATIVA", "INATIVO", "INATIVA", "REGULAR", "IRREGULAR", "COREN", "INSCRI", "REGISTRO"]):
                if not re.fullmatch(r"\d{4,}", part):
                    found_name = part
                    continue
            if status_text is None and any(token in upper for token in ["ATIVO", "ATIVA", "INATIVO", "INATIVA", "SUSPENS", "CANCEL", "BAIXAD", "REGULAR", "IRREGULAR"]):
                status_text = part
                continue
            if parsed_registration_number is None:
                number_match = re.search(r"\d{4,}", part)
                if number_match:
                    parsed_registration_number = number_match.group(0)

        return {
            "found_name": found_name,
            "registration_number": parsed_registration_number or registration_number,
            "found_state": state or "SP",
            "profession": "ENFERMAGEM",
            "status_text": status_text,
        }

    async def search_by_name(self, full_name: str, state: str | None = None) -> list[dict[str, Any]]:
        raise RuntimeError("Este conector do COREN-SP foi desenhado para busca por número de inscrição. Use o runner específico por registro.")

    async def search_by_registration(self, registration_number: str, state: str | None = None) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        logger.info("Iniciando consulta por inscrição no %s para %s", self.council_name, registration_number)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=False, slow_mo=400)
            page = await browser.new_page(viewport={"width": 1440, "height": 900})

            try:
                await page.goto(self.search_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2500)

                print("URL inicial:", page.url)
                print("Título inicial:", await page.title())

                criterion_selected = await self._select_registration_criterion(page)
                print("Critério por inscrição selecionado:", criterion_selected)
                await page.wait_for_timeout(1000)

                registration_input_selectors = [
                    'input[name*="inscr" i]',
                    'input[id*="inscr" i]',
                    'input[placeholder*="inscr" i]',
                    'input[name*="registro" i]',
                    'input[id*="registro" i]',
                    'input[placeholder*="registro" i]',
                    'input[name*="numero" i]',
                    'input[id*="numero" i]',
                    'input[placeholder*="numero" i]',
                    'input[type="text"]',
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
                    'main *',
                ]

                normalized_registration = registration_number.replace("-SP", "").replace(" ", "")
                used_input_selector = await self._fill_first_visible(page, registration_input_selectors, normalized_registration)
                print("Campo usado:", used_input_selector)
                print("Inscrição preenchida:", normalized_registration)

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

                await page.screenshot(path="coren_sp_registration_debug_v3.png", full_page=True)
                with open("coren_sp_registration_debug_v3.html", "w", encoding="utf-8") as f:
                    f.write(html)

                candidate_rows = []
                for selector in results_container_selectors:
                    rows = await page.query_selector_all(selector)
                    if rows:
                        print(f"Seletor de resultado com matches: {selector} -> {len(rows)}")
                        candidate_rows.extend(rows)

                seen_texts = set()
                for row in candidate_rows:
                    raw_text = (await row.inner_text()).strip()
                    if not raw_text or raw_text in seen_texts:
                        continue
                    seen_texts.add(raw_text)

                    if self._is_form_header_noise(raw_text):
                        continue

                    upper_text = raw_text.upper()
                    has_registration_signal = normalized_registration in upper_text or any(token in upper_text for token in ["ATIVO", "ATIVA", "INATIVO", "INATIVA", "COREN", "INSCRI", "REGISTRO", "ENFERMAG"])
                    if not has_registration_signal:
                        continue

                    parsed = self._parse_result_block(raw_text, normalized_registration, state)
                    if not parsed.get("found_name") and not parsed.get("status_text"):
                        continue

                    parsed["evidence_url"] = page.url
                    parsed["evidence_note"] = "Resultado capturado por template Playwright V3 de busca por inscrição do COREN-SP."
                    parsed["notes"] = "Conector em modo de homologação por número de inscrição; critério explícito selecionado antes do preenchimento."
                    results.append(parsed)

                if not results:
                    logger.info("Nenhum resultado localizado para inscrição %s no %s", normalized_registration, self.council_name)

                return results

            except PlaywrightTimeoutError:
                logger.exception("Timeout na consulta %s para inscrição %s", self.council_name, registration_number)
                raise RuntimeError(f"Timeout na consulta do conselho {self.council_name}")
            except Exception:
                logger.exception("Falha na consulta %s para inscrição %s", self.council_name, registration_number)
                raise
            finally:
                await browser.close()

    def parse_result(self, raw_item: dict[str, Any], searched_name: str, searched_state: str | None = None) -> dict[str, Any]:
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
