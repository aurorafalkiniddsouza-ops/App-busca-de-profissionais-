# Smoke test do conector COREN-SP

Este teste valida a trilha unitária do COREN-SP sem alterar o baseline do CREMESP.

## Pré-requisitos

```bash
pip install -r requirements.txt
python -m playwright install
```

## Execução

```bash
python scripts/run_coren_sp_smoke_test_local.py "NOME DO PROFISSIONAL"
```

## Resultado esperado

- se o portal responder e os seletores forem minimamente compatíveis, a saída será uma lista JSON
- se houver proteção, timeout ou mudança de HTML, a execução deve falhar com erro controlado ou retornar lista vazia

## Critérios de análise

1. O campo é preenchido corretamente
2. O submit dispara a pesquisa
3. O portal retorna resultados ou sinaliza bloqueio/proteção
4. O HTML permite capturar:
   - nome
   - situação
   - número de inscrição, se disponível

## Próxima ação

Após a primeira execução bem-sucedida, refinar os seletores e estruturar o parsing do retorno bruto.
