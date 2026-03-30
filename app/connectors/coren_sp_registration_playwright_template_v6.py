from __future__ import annotations

import re
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.connectors.base import BaseCouncilConnector
from app.infra.logger import get_logger

logger = get_logger()


class CorenSPRegistrationPlaywrightTemplateV6Connector(BaseCouncilConnector):
    council_name = "COREN-SP"
    search_url = "https://servicos.coren-sp.gov.br/consulta-de-profissionais/"

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

    def _extract_from_window(self, text: str, normalized_registration: str, state: str | None) -> dict[str, Any] | None:
        compact_digits = re.sub(r"\D", "", text)
        if normalized_registration not in compact_digits:
            return None

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return None

        found_name = None
        status_text = None
        registration_number = normalized_registration

        for line in lines:
            upper = line.upper()
            if status_text is None and any(token in upper for token in ["ATIVO", "ATIVA", "INATIVO", "INATIVA", "REGULAR", "IRREGULAR", "SUSPENS", "CANCEL", "BAIXAD"]):
                status_text = line
                continue
            if any(token in upper for token in ["CRITÉRIO PARA PESQUISA", "CRITERIO PARA PESQUISA", "NÚMERO DA INSCRIÇÃO", "NUMERO DA INSCRICAO", "CONSULTAR"]):
                continue
            if found_name is None and not re.search(r"\d{4,}", line):
                if not any(token in upper for token in ["COREN", "INSCRI", "REGISTRO", "ENFERMAG"]):
                    found_name = line

        if not found_name and not status_text:
            return None

        return {
            "found_name": found_name,
            "registration_number": registration_number,
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

                normalized_registration = re.sub(r"\D", "", registration_number)
                used_input_selector = None
                active_input = None
                for selector in registration_input_selectors:
                    locator = page.locator(selector)
                    count = await locator.count()
                    if count == 0:
                        continue
                    for index in range(count):
                        element = locator.nth(index)
                        try:
                            if await element.is_visible() and await element.is_enabled():
                                await element.click()
                                await element.fill("")
                                await element.fill(normalized_registration)
                                await element.dispatch_event("input")
                                await element.dispatch_event("change")
                                await element.dispatch_event("blur")
                                used_input_selector = selector
                                active_input = element
                                break
                        except Exception:
                            continue
                    if used_input_selector:
                        break

                if not used_input_selector:
                    raise RuntimeError("Campo de número de inscrição não localizado no portal COREN-SP")

                print("Campo usado:", used_input_selector)
                print("Inscrição preenchida:", normalized_registration)

                used_submit_selector = await self._click_first_visible(page, submit_selectors)
                if used_submit_selector:
                    print("Botão usado:", used_submit_selector)
                if active_input is not None:
                    try:
                        await active_input.press("Enter")
                        print("Enter enviado no campo de inscrição")
                    except Exception:
                        pass
                try:
                    await page.locator("form").first.evaluate("(form) => form.requestSubmit ? form.requestSubmit() : form.submit()")
                    print("Submit do formulário disparado")
                except Exception:
                    print("Submit do formulário não pôde ser disparado diretamente")

                await page.wait_for_timeout(5000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                body_text = await page.locator("body").inner_text()
                print("BODY TEXT PARCIAL:")
                print(body_text[:3000])
                with open("coren_sp_registration_body_v6.txt", "w", encoding="utf-8") as f:
                    f.write(body_text)

                print("URL final:", page.url)
                print("Título final:", await page.title())

                html = await page.content()
                await page.screenshot(path="coren_sp_registration_debug_v6.png", full_page=True)
                with open("coren_sp_registration_debug_v6.html", "w", encoding="utf-8") as f:
                    f.write(html)

                digit_text = re.sub(r"\D", "", body_text)
                if normalized_registration in digit_text:
                    idx = digit_text.find(normalized_registration)
                    print("Número da inscrição encontrado no texto integral da página")
                else:
                    idx = -1
                    print("Número da inscrição NÃO encontrado no texto integral da página")

                if idx >= 0:
                    windows = []
                    for match in re.finditer(normalized_registration, digit_text):
                        approx_pos = match.start()
                        start = max(0, approx_pos - 800)
                        end = min(len(body_text), approx_pos + 800)
                        windows.append(body_text[start:end])
                    for window in windows:
                        parsed = self._extract_from_window(window, normalized_registration, state)
                        if parsed:
                            parsed["evidence_url"] = page.url
                            parsed["evidence_note"] = "Resultado capturado por template Playwright V6 de busca por inscrição do COREN-SP."
                            parsed["notes"] = "Conector em modo de homologação por número de inscrição; extração ancorada no texto integral aplicada."
                            results.append(parsed)
                            break

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
