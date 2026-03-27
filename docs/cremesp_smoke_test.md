# Smoke test do conector CREMESP

Este teste valida primeiro o fluxo Playwright do CREMESP antes de promover o conector para o pipeline principal.

## Pré-requisitos

```bash
pip install -r requirements.txt
playwright install
```

## Execução

```bash
python scripts/run_cremesp_smoke_test.py "NOME DO PROFISSIONAL"
```

## Resultado esperado

- Se houver retorno navegável no portal, o script imprime uma lista JSON de resultados.
- Se os seletores placeholder não forem compatíveis com o HTML atual, a execução deve falhar com erro controlado.
- Se não houver resultado visível para o nome consultado, a saída deve ser `[]`.

## Critérios de homologação

1. O campo de busca é preenchido corretamente.
2. O submit dispara a pesquisa sem erro.
3. O portal retorna resultados navegáveis sem bloqueio impeditivo.
4. O HTML dos resultados permite capturar ao menos:
   - nome
   - evidência da URL
5. O conector consegue ser refinado para extrair CRM, UF e situação.

## Próxima ação após teste

Se o smoke test funcionar, promover a implementação do template para `app/connectors/cremesp.py` e conectar o `registry.py` ao conector real.
