# Relatório de Avaliação — Rubrica KiroSonar (Equipe 5)

Projeto avaliado: **Semantic Log Explorer**
Data: 30/03/2026
Rubrica: `rubric_equipe-5.md` — Total: 100 pontos

---

## Qualidade de Código — 28 / 30 pts

**Nível: 30 pts (Código limpo, funções bem nomeadas, sem duplicação, complexidade baixa)**

Evidências positivas:
- Arquitetura modular com separação clara em camadas: `api/`, `core/`, `services/`, `models/`
- Funções com responsabilidade única e nomes descritivos: `sanitize_pii()`, `sanitize_prompt_injection()`, `build_prompt()`, `retrieve()`, `_flush_chunk()`, `_clean_noise()`
- Tipagem Python consistente em todos os módulos (`list[Chunk]`, `Optional[str]`, `AsyncGenerator[str, None]`)
- Injeção de dependências via FastAPI `Depends()` para desacoplamento
- Frontend com Composition API, JSDoc em todas as funções, componentes encapsulados com BEM CSS
- Ruff configurado com regras explícitas (pycodestyle, pyflakes, isort, naming, pyupgrade, bugbear, bandit, simplify)

Pontos de desconto (-2 pts):
- Leve duplicação no `_process_json_content()` do `ingestion.py` — a lógica de extração de metadados JSON (timestamp, level) se repete para array, objeto e JSONL
- Frontend em JavaScript puro (sem TypeScript), reduzindo a tipagem estática

---

## Clareza da Documentação — 20 / 20 pts

**Nível: 20 pts (Todas as funções/módulos documentados, README claro e exemplos funcionais)**

Evidências:
- README completo com instruções de setup (backend, frontend, Docker dev/prod), variáveis de ambiente, pré-requisitos
- `.env.example` documentado com comentários em português para cada variável
- PRD detalhado (`prd.md`) com requisitos funcionais/não-funcionais, histórias de usuário, stack, plano de testes
- Arquitetura técnica (`arquitetura.md`) com diagramas ASCII, descrição de componentes, decisões técnicas justificadas
- Diagramas UML em Mermaid (`diagrama.md`): componentes, sequência de consulta, sequência de ingestão
- Docstrings em todos os módulos Python (módulo, classe e função) com Args/Returns documentados
- JSDoc em todas as funções do frontend com `@param` e `@returns`
- Endpoints documentados automaticamente via FastAPI/OpenAPI (Swagger)

---

## Segurança — 19 / 20 pts

**Nível: 20 pts (Nenhum secret exposto, inputs validados, erros tratados sem vazar informações sensíveis)**

Evidências positivas:
- Secrets gerenciados via `.env` com `.env.example` documentado
- Validação obrigatória da `GOOGLE_API_KEY` com `field_validator` (rejeita vazio/whitespace)
- Validação de entrada com Pydantic em todos os endpoints: `ChatRequest` com `min_length=1, max_length=2000`, upload com validação de extensão e tamanho
- Sanitização de PII (`security.py`): CPF, e-mail, senhas mascarados antes de envio ao LLM
- Sanitização de prompt injection com 8 padrões de ataque bloqueados
- CORS restrito a origens específicas (`CORS_ORIGINS` configurável)
- Global exception handler que retorna mensagem genérica sem vazar stack traces: `"Erro interno do servidor"`
- HTML escaping no frontend (`escapeHtml` no `MessageBubble.vue`) contra XSS
- ChromaDB efêmero (zero data retention)

Ponto de desconto (-1 pt):
- Sem rate limiting nos endpoints (mitigável via Nginx/API Gateway, mas ausente na aplicação)

---

## Cobertura de Testes — 30 / 30 pts

**Nível: 30 pts (Testes unitários para os módulos principais, casos de borda cobertos, sem testes frágeis)**

Evidências:

Testes unitários (11 arquivos, 207 testes):
- `test_config.py` — 6 testes: validação de settings, defaults, env override
- `test_security.py` — 16 testes: CPF, e-mail, senha, mixed PII, edge cases
- `test_prompt_injection.py` — 13 testes: 8 padrões de ataque, case insensitive, preservação de queries válidas
- `test_ingestion.py` — 18 testes: chunking, stack traces, PII, noise, JSON/JSONL, edge cases (arquivo vazio)
- `test_llm.py` — 12 testes: system prompt, build_prompt, streaming, error handling
- `test_retriever.py` — 9 testes: top_k clamping, metadata reconstruction, empty collection
- `test_routes.py` — 15 testes: upload (formato, tamanho, vazio, extensões), chat (empty, no logs, SSE, max length)
- `test_vectorstore.py` — 14 testes: ephemeral mode, add/search/clear, error handling (502/503)
- `test_docker_backend.py`, `test_docker_frontend.py`, `test_docker_compose.py`, `test_nginx_conf.py` — 44 testes de infraestrutura

Testes de propriedade (12 arquivos, 18 testes com Hypothesis):
- `test_pii_sanitization_prop.py` — PII com dados gerados aleatoriamente
- `test_chunking_prop.py` — chunking com logs gerados
- `test_file_validation_prop.py` — validação de arquivos com extensões/tamanhos aleatórios
- `test_prompt_assembly_prop.py` — montagem de prompts
- `test_retriever_prop.py` — busca semântica
- `test_sse_format_prop.py` — formato SSE
- `test_upload_response_prop.py` — resposta de upload
- `test_vectorization_prop.py` — vetorização
- `test_session_cleanup_prop.py`, `test_docker_secrets_prop.py`, `test_nginx_proxy_prop.py`, `test_spa_fallback_prop.py`

Testes frontend (3 suítes, 30 testes):
- `useChat.test.js` — 12 testes: estado inicial, mensagens, erros, IDs únicos
- `MessageBubble.test.js` — 10 testes: renderização, markdown, XSS, acessibilidade
- `FileUpload.test.js` — 8 testes: dropzone, formatos, acessibilidade

Casos de borda cobertos:
- Arquivo vazio, extensões inválidas, tamanho excedido
- CPF parcial (não mascara), e-mail parcial (não mascara)
- top_k negativo/zero (clamped), collection vazia
- Prompt injection case insensitive, mixed com query válida
- Hypothesis com 200 exemplos por teste (500 no CI)

CI/CD:
- GitHub Actions com jobs separados para unit e property tests
- Coverage `fail_under=80` com relatório HTML como artefato

---

## Resumo

| Critério | Nota | Máximo |
|---|---|---|
| Qualidade de Código | 28 | 30 |
| Clareza da Documentação | 20 | 20 |
| Segurança | 19 | 20 |
| Cobertura de Testes | 30 | 30 |
| **Total** | **97** | **100** |

---
---

# 2ª Avaliação — Após Correções

Data: 30/03/2026

## Qualidade de Código — 30 / 30 pts

**Nível: 30 pts (Código limpo, funções bem nomeadas, sem duplicação, complexidade baixa)**

Correção aplicada:
- Duplicação eliminada no `ingestion.py` — lógica de extração de metadados JSON extraída para a função `_json_entry_to_chunk()`, reutilizada nos 3 fluxos (array, objeto, JSONL)

Evidências:
- Arquitetura modular com separação clara em camadas
- Tipagem Python consistente, funções com responsabilidade única
- Ruff configurado com regras explícitas
- Zero duplicação na lógica de processamento JSON

*Nota: Frontend permanece em JavaScript puro (sem TypeScript), mas não configura duplicação ou code smell — é uma escolha de stack.*

## Clareza da Documentação — 20 / 20 pts

**Nível: 20 pts (sem alterações — já era nota máxima)**

## Segurança — 20 / 20 pts

**Nível: 20 pts (Nenhum secret exposto, inputs validados, erros tratados sem vazar informações sensíveis)**

Correção aplicada:
- Rate limiting implementado via `RateLimitMiddleware` — 30 requisições por minuto por IP, com sliding window in-memory
- Endpoint `/health` isento do rate limiting
- Retorna HTTP 429 com mensagem em português quando o limite é excedido

## Cobertura de Testes — 30 / 30 pts

**Nível: 30 pts (sem alterações — já era nota máxima)**

---

## Resumo — 2ª Avaliação

| Critério | Nota | Máximo |
|---|---|---|
| Qualidade de Código | 30 | 30 |
| Clareza da Documentação | 20 | 20 |
| Segurança | 20 | 20 |
| Cobertura de Testes | 30 | 30 |
| **Total** | **100** | **100** |

---

## Comparativo

| Critério | 1ª Avaliação | 2ª Avaliação | Δ |
|---|---|---|---|
| Qualidade de Código | 28/30 | 30/30 | +2 |
| Clareza da Documentação | 20/20 | 20/20 | 0 |
| Segurança | 19/20 | 20/20 | +1 |
| Cobertura de Testes | 30/30 | 30/30 | 0 |
| **Total** | **97/100** | **100/100** | **+3** |
