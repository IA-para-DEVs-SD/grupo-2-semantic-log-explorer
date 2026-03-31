# Rubric de Qualidade - KiroSonar
Total: **100 pontos** | 5 critérios (4 obrigatórios + 1 próprio do time)
| Critério | Peso | Descrição |
|---|---|---|
| Qualidade de código | 30 pts | Clareza, organização, boas práticas, ausência de code smells e complexidade desnecessária |
| Clareza da documentação | 20 pts | Docstrings, comentários relevantes, README atualizado e exemplos de uso |
| Segurança | 20 pts | Ausência de secrets expostos, validação de inputs, tratamento seguro de erros |
| Critério próprio do time | 30 pts | Cobertura de testes: presença de testes unitários significativos, casos de borda cobertos e ausência de testes frágeis |
## Detalhamento dos Critérios
### Qualidade de código (30 pts)
- 30 pts: Código limpo, funções bem nomeadas, sem duplicação, complexidade baixa
- 20 pts: Pequenos problemas de estilo ou leve duplicação, mas legível
- 10 pts: Código funcional mas com problemas evidentes de organização
- 0 pts: Código confuso, sem estrutura ou com erros graves de design
### Clareza da documentação (20 pts)
- 20 pts: Todas as funções/módulos documentados, README claro e exemplos funcionais
- 13 pts: Documentação parcial, cobre os pontos principais
- 7 pts: Documentação mínima ou desatualizada
- 0 pts: Sem documentação relevante
### Segurança (20 pts)
- 20 pts: Nenhum secret exposto, inputs validados, erros tratados sem vazar informações sensíveis
- 13 pts: Pequenas falhas não críticas
- 7 pts: Falhas moderadas que podem ser exploradas
- 0 pts: Secrets expostos ou vulnerabilidades críticas presentes
### Cobertura de testes — critério próprio do time (30 pts)
- 30 pts: Testes unitários para os módulos principais, casos de borda cobertos, sem testes frágeis
- 20 pts: Boa cobertura dos fluxos principais, poucos casos de borda
- 10 pts: Testes existem mas cobrem apenas o caminho feliz
- 0 pts: Sem testes ou testes que não validam comportamento real