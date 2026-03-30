# Smoke test do conector COREN-SP por número de inscrição

Este teste valida a trilha unitária do COREN-SP usando **número de inscrição**, sem alterar o baseline do CREMESP.

## Pré-requisitos

```bash
pip install -r requirements.txt
python -m playwright install
```

## Execução

```bash
python scripts/run_coren_sp_registration_smoke_test_local.py "NUMERO_DE_INSCRICAO"
```

## Resultado esperado

- se o portal responder e os seletores forem compatíveis, a saída será uma lista JSON
- se houver proteção, timeout ou mudança de HTML, a execução deve falhar com erro controlado ou retornar lista vazia

## Critérios de análise

1. O campo de número de inscrição é preenchido corretamente
2. O submit dispara a pesquisa
3. O portal retorna resultado ou sinaliza bloqueio/proteção
4. O HTML permite capturar:
   - nome
   - situação
   - número de inscrição

## Artefatos de debug

A execução gera artefatos locais para análise:
- `coren_sp_registration_debug.png`
- `coren_sp_registration_debug.html`

## Próxima ação

Após a primeira execução bem-sucedida, refinar os seletores e estruturar o parsing do retorno bruto.
