# Runbook de operação local — CREMESP

## Objetivo

Executar localmente o fluxo validado de consulta em lote do CREMESP usando Streamlit no Windows.

## Pré-requisitos

- Python instalado
- Git instalado
- Ambiente virtual criado em `.venv`
- Dependências instaladas via `requirements.txt`
- Playwright instalado

## Comando oficial atual

```bat
cd C:\Users\vinicius.pereira\App-busca-de-profissionais-
git pull
.venv\Scripts\activate
streamlit run app/ui/streamlit_app_streamlit_file_safe_local.py
```

## Formato mínimo da planilha

A planilha deve conter a coluna:

- `nome`

## Fluxo operacional

1. Abrir o app local no navegador
2. Selecionar `CREMESP`
3. Definir a pausa entre nomes
4. Fazer upload da planilha
5. Clicar em `Processar consultas`
6. Validar o resumo executivo
7. Baixar o resultado em Excel

## Campos esperados na saída

- `searched_name`
- `council`
- `final_status`
- `found_name`
- `registration_number`
- `status_text`
- `confidence_score`
- `notes`
- `queried_at`

## Recomendações operacionais

- Rodar inicialmente lotes menores para homologação
- Manter evidência dos arquivos de entrada e saída
- Validar amostras manualmente
- Ajustar pausa entre nomes se houver degradação do portal

## Diagnóstico rápido

### Caso `ERRO NA CONSULTA`
Verificar:
- coluna `notes`
- estabilidade do portal
- se o nome consultado está correto
- se o ambiente virtual está ativo

### Caso `NÃO ENCONTRADO`
Verificar:
- grafia do nome
- presença de sobrenome composto
- necessidade de conferência manual

## Próxima expansão

Após estabilização do CREMESP, replicar o fluxo para COREN-SP com a mesma abordagem de homologação incremental.
