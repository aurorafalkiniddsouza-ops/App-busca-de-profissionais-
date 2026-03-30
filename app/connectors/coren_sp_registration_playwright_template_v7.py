from __future__ import annotations

import re
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.connectors.base import BaseCouncilConnector
from app.infra.logger import get_logger

logger = get_logger()


class CorenSPRegistrationPlaywrightTemplateV7Connector(BaseCouncilConnector):
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

    def _parse_candidate_text(self, text: str, normalized_registration: str, state: str | None) -> dict[str, Any] | None:
        cleaned = text.replace("\r", "\n").strip()
        if not cleaned:
            return None
        upper = cleaned.upper()
        noise_markers = [
            "CRITÉRIO PARA PESQUISA",
            "CRITERIO PARA PESQUISA",
            "NÚMERO DA INSCRIÇÃO",
            "NUMERO DA INSCRICAO",
            "VALOR PARA PESQUISA",
        ]
        if any(marker in upper for marker in noise_markers) and len(cleaned.splitlines()) < 12:
            return None

        digits_only = re.sub(r"\D", "", cleaned)
        has_registration = normalized_registration in digits_only
        has_status = any(token in upper for token in ["ATIVO", "ATIVA", "INATIVO", "INATIVA", "REGULAR", "IRREGULAR", "SUSPENS", "CANCEL", "BAIXAD"])
        if not has_registration and not has_status:
            return None

        parts = [part.strip() for part in re.split(r"\t+|\n+", cleaned) if part.strip()]
        found_name = None
        status_text = None
        parsed_registration_number = None

        for part in parts:
            upper_part = part.upper()
            if status_text is None and any(token in upper_part for token in ["ATIVO", "ATIVA", "INATIVO", "INATIVA", "REGULAR", "IRREGULAR", "SUSPENS", "CANCEL", "BAIXAD"]):
                status_text = part
                continue
            if parsed_registration_number is None:
                match = re.search(r"\d{4,}", part)
                if match:
                    parsed_registration_number = match.group(0)
            if found_name is None and not re.search(r"\d{4,}", part):
                if not any(token in upper_part for token in ["COREN", "INSCRI", "REGISTRO", "ENFERMAG", "RESULTADO DA CONSULTA", "TIPO DE INSCRI"]):
                    found_name = part

        if not found_name and not status_text:
            return None

        return {
            "found_name": found_name,
            "registration_number": parsed_registration_number or normalized_registration,
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

                print("URL final:", page.url)
                print("Título final:", await page.title())

                frame_texts: list[tuple[str, str]] = []
                for idx, frame in enumerate(page.frames):
                    try:
                        frame_body = await frame.locator("body").inner_text(timeout=3000)
                        label = f"frame[{idx}] {frame.url}"
                        frame_texts.append((label, frame_body))
                    except Exception:
                        continue

                with open("coren_sp_registration_frames_v7.txt", "w", encoding="utf-8") as f:
                    for label, text in frame_texts:
                        f.write(f"===== {label} =====\n")
                        f.write(text)
                        f.write("\n\n")

                for label, text in frame_texts:
                    print(f"FRAME TEXTO CAPTURADO: {label}")
                    print(text[:2000])

                html = await page.content()
                await page.screenshot(path="coren_sp_registration_debug_v7.png", full_page=True)
                with open("coren_sp_registration_debug_v7.html", "w", encoding="utf-8") as f:
                    f.write(html)

                for label, text in frame_texts:
                    parsed = self._parse_candidate_text(text, normalized_registration, state)
                    if parsed:
                        parsed["evidence_url"] = page.url
                        parsed["evidence_note"] = f"Resultado capturado por template Playwright V7 de busca por inscrição do COREN-SP a partir de {label}."
                        parsed["notes"] = "Conector em modo de homologação por número de inscrição; leitura de frames/iframes aplicada."
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
