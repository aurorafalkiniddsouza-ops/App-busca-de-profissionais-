# Plano de homologação — COREN-SP

## Objetivo

Iniciar a homologação do conector do **COREN-SP** sem alterar o baseline já validado do **CREMESP**.

## Princípio de segurança

Toda a trilha do COREN-SP deve permanecer isolada do fluxo atual do CREMESP.

Isso significa:
- não substituir o app atual usado em produção assistida
- não trocar o registry estável do CREMESP
- não reutilizar runners do CREMESP para COREN-SP

## Estratégia de implementação

### Fase 1 — Consulta unitária

1. Criar um template dedicado para COREN-SP
2. Testar 1 nome por vez
3. Inspecionar HTML real, resultado, possíveis proteções e comportamento do portal
4. Confirmar quais campos podem ser capturados:
   - nome
   - número de inscrição
   - situação
   - evidência de URL

### Fase 2 — Parsing estruturado

Separar o retorno bruto em:
- `found_name`
- `registration_number`
- `status_text`
- `found_state`
- `profession`

### Fase 3 — Runner individual

Criar um runner isolado para teste unitário do COREN-SP.

### Fase 4 — Runner por arquivo

Somente após a validação unitária.

### Fase 5 — Interface local segura

Integrar ao Streamlit apenas depois que a rota unitária estiver consistente.

## Critérios de avanço

O COREN-SP só deve avançar para lote quando:
- a consulta unitária funcionar
- o parsing retornar campos estruturados
- o portal se mostrar estável
- os erros conhecidos estiverem documentados

## Riscos conhecidos

- possíveis proteções anti-bot
- mudança frequente de HTML
- múltiplos resultados por nome
- baixa previsibilidade da estrutura do portal

## Meta da próxima entrega

- runner individual do COREN-SP
- conector dedicado em homologação
- documentação de debug local
