# Rubrica de Qualidade — Mundialito

Rubrica de avaliação técnica para o projeto **Semantic Log Explorer**, totalizando **100 pontos**.

| Critério | Abaixo do esperado (0 pts) | Atende parcialmente | Excelente (pontuação máxima) |
|---|---|---|---|
| **Qualidade de Código (30 pts)** | Código sem padronização, sem tipagem, funções extensas e acopladas, ausência de linting/formatação, nomes de variáveis genéricos ou inconsistentes. | **(15 pts)** Código parcialmente padronizado, tipagem presente em parte dos módulos, algumas funções ainda extensas ou com responsabilidades mistas, linting configurado mas com violações pendentes. | **(30 pts)** Código limpo, tipado, modular e coeso. Funções com responsabilidade única, nomes descritivos, linting (Ruff) e formatação aplicados sem violações. Separação clara entre camadas (API, serviços, modelos). |
| **Clareza da Documentação (20 pts)** | Sem README funcional, sem instruções de setup, sem descrição da arquitetura ou dos endpoints. Documentação inexistente ou desatualizada. | **(10 pts)** README com instruções básicas de instalação e execução, mas sem detalhamento da arquitetura, fluxo de dados ou descrição dos endpoints da API. | **(20 pts)** README completo com setup, variáveis de ambiente e comandos. Documentação da arquitetura (diagramas), PRD atualizado, endpoints documentados via OpenAPI/Swagger gerado pelo FastAPI. |
| **Segurança (20 pts)** | Secrets hardcoded no código, sem validação de entrada, sem sanitização de dados, endpoints expostos sem autenticação, dependências com vulnerabilidades conhecidas. | **(10 pts)** Secrets em variáveis de ambiente mas sem rotação ou gestão adequada, validação de entrada parcial (alguns endpoints sem Pydantic), CORS configurado mas permissivo. | **(20 pts)** Secrets gerenciados via `.env` com `.env.example` documentado, validação de entrada com Pydantic em todos os endpoints, CORS restrito, sanitização contra prompt injection, dependências auditadas e sem CVEs críticas. |
| **Testes Automatizados (30 pts)** | Sem testes ou com testes triviais que não validam comportamento real. Sem cobertura mensurável, sem execução em CI. | **(15 pts)** Testes unitários cobrindo parte dos serviços e rotas, cobertura entre 40–70%, ausência de testes de propriedade ou de integração, execução manual apenas. | **(30 pts)** Testes unitários e de propriedade cobrindo serviços, rotas e modelos. Cobertura ≥ 80% mensurável (pytest-cov). Testes executados em CI (GitHub Actions) com falha bloqueante no PR. |

## Resumo da Pontuação

| Critério | Peso |
|---|---|
| Qualidade de Código | 30 pts |
| Clareza da Documentação | 20 pts |
| Segurança | 20 pts |
| Testes Automatizados | 30 pts |
| **Total** | **100 pts** |
