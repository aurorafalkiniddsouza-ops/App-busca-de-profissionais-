# Próximos passos — CREMESP estabilizado e expansão para COREN-SP

## Situação atual

O fluxo validado localmente em Windows para o **CREMESP** já demonstrou viabilidade operacional:

- consulta individual funcionando
- processamento em lote funcionando
- saída estruturada com:
  - `found_name`
  - `registration_number`
  - `status_text`
  - `final_status`
- rota estável via **Streamlit + subprocesso + JSON temporário**

## Próxima sprint recomendada

### Frente 1 — Oficialização do CREMESP

1. Congelar a rota validada como baseline
2. Consolidar o conector do CREMESP como conector oficial
3. Promover o app file-safe como interface padrão local
4. Documentar dependências e comando oficial de execução
5. Criar uma bateria de regressão com nomes conhecidos

### Frente 2 — Qualidade e governança

1. Validar 20 a 50 nomes reais
2. Medir taxa de:
   - ATIVO correto
   - não encontrado correto
   - erro de consulta
3. Criar planilha de homologação manual
4. Manter evidências dos lotes processados
5. Registrar limitações conhecidas

### Frente 3 — Expansão para COREN-SP

1. Reaproveitar a mesma arquitetura do CREMESP
2. Validar consulta unitária
3. Mapear HTML real e proteções do portal
4. Criar runner individual
5. Criar runner por arquivo
6. Integrar ao Streamlit seguro

## Critérios de promoção do CREMESP para produção oficial

- 0 falhas estruturais no fluxo local
- taxa de retorno correta aceitável em amostra validada
- output padronizado consistente
- app local funcionando para lote pequeno e médio
- logging mínimo disponível

## Meta técnica da próxima etapa

### Objetivo A
Transformar o CREMESP em conector oficial do projeto.

### Objetivo B
Iniciar homologação real do COREN-SP com o mesmo padrão arquitetural.

## Comando recomendado atual

```bat
streamlit run app/ui/streamlit_app_streamlit_file_safe_local.py
```

## Resultado esperado nas próximas entregas

- projeto com um conector oficial consolidado
- segundo conector em homologação real
- fluxo de lote com menor risco operacional
- base pronta para futura execução em servidor ou nuvem
