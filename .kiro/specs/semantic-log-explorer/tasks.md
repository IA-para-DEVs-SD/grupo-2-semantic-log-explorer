# Tarefas de Implementação — Semantic Log Explorer

## 1. Configuração e Infraestrutura do Backend
- [x] 1.1 Criar `backend/src/models/schemas.py` com os modelos Pydantic (LogLevel, ChunkMetadata, Chunk, UploadResponse, ChatRequest, ErrorResponse)
- [x] 1.2 Criar `backend/src/core/config.py` com classe Settings (BaseSettings) carregando GOOGLE_API_KEY, CHROMA_COLLECTION_NAME, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS do .env
- [x] 1.3 Criar `backend/src/api/dependencies.py` com providers de injeção de dependência para Settings, VectorStoreService e LLMService
- [x] 1.4 Atualizar `backend/.env.example` com todas as variáveis de ambiente necessárias (GOOGLE_API_KEY, CHROMA_COLLECTION_NAME)
- [x] 1.5 Atualizar `backend/src/main.py` para registrar rotas de upload e chat e configurar middleware de erro global

## 2. Sanitização de PII
- [x] 2.1 Criar `backend/src/core/security.py` com função `sanitize_pii(text: str) -> str` usando Regex para CPF, e-mail e senhas, substituindo por marcadores [CPF_MASCARADO], [EMAIL_MASCARADO], [SENHA_MASCARADA]
- [x] 2.2 Escrever testes unitários em `backend/tests/unit/test_security.py` para sanitização de PII com exemplos específicos e edge cases
- [x] 2.3 [PBT] Escrever teste de propriedade em `backend/tests/property/test_pii_sanitization_prop.py` — Feature: semantic-log-explorer, Property 5: Sanitização de PII remove todos os dados sensíveis

## 3. Ingestão e Chunking de Logs
- [x] 3.1 Criar `backend/src/services/ingestion.py` com função `process_file` que executa limpeza, sanitização PII e chunking semântico por evento/stack trace
- [x] 3.2 Escrever testes unitários em `backend/tests/unit/test_ingestion.py` para processamento de arquivos .log, .txt e .json
- [x] 3.3 [PBT] Escrever teste de propriedade em `backend/tests/property/test_chunking_prop.py` — Feature: semantic-log-explorer, Property 2: Chunking preserva stack traces completos

## 4. VectorStore — Interface ChromaDB
- [x] 4.1 Criar `backend/src/services/vectorstore.py` com classe VectorStoreService (ChromaDB efêmero, embeddings via text-embedding-004, métodos add_chunks, search, clear_collection)
- [x] 4.2 Escrever testes unitários em `backend/tests/unit/test_vectorstore.py` para operações do ChromaDB (modo efêmero, limpeza de coleção)
- [x] 4.3 [PBT] Escrever teste de propriedade em `backend/tests/property/test_vectorization_prop.py` — Feature: semantic-log-explorer, Property 4: Vetorização produz embeddings e metadados corretos
- [x] 4.4 [PBT] Escrever teste de propriedade em `backend/tests/property/test_session_cleanup_prop.py` — Feature: semantic-log-explorer, Property 8: Limpeza de sessão remove todos os dados

## 5. Retriever — Busca Semântica
- [x] 5.1 Criar `backend/src/services/retriever.py` com função `retrieve(question, top_k)` que converte pergunta em vetor e busca chunks por similaridade de cosseno
- [x] 5.2 Escrever testes unitários em `backend/tests/unit/test_retriever.py` para busca semântica
- [x] 5.3 [PBT] Escrever teste de propriedade em `backend/tests/property/test_retriever_prop.py` — Feature: semantic-log-explorer, Property 6: Retriever retorna quantidade limitada de resultados

## 6. Serviço LLM — Integração Gemini
- [x] 6.1 Criar `backend/src/services/llm.py` com classe LLMService (prompt de sistema SRE Senior, método generate_stream com streaming assíncrono via Gemini)
- [x] 6.2 Escrever testes unitários em `backend/tests/unit/test_llm.py` para montagem de prompt e instrução contra especulação
- [x] 6.3 [PBT] Escrever teste de propriedade em `backend/tests/property/test_prompt_assembly_prop.py` — Feature: semantic-log-explorer, Property 7: Montagem do prompt inclui papel e contexto

## 7. Rotas da API (Upload e Chat)
- [x] 7.1 Criar `backend/src/api/routes/upload.py` com POST /api/upload (validação de formato e tamanho, orquestração do pipeline de ingestão)
- [x] 7.2 Criar `backend/src/api/routes/chat.py` com POST /api/chat (orquestração retriever → LLM → StreamingResponse SSE)
- [x] 7.3 Escrever testes unitários em `backend/tests/unit/test_routes.py` para rotas de upload e chat (validações, edge cases, erros)
- [x] 7.4 [PBT] Escrever teste de propriedade em `backend/tests/property/test_file_validation_prop.py` — Feature: semantic-log-explorer, Property 1: Validação de formato de arquivo
- [x] 7.5 [PBT] Escrever teste de propriedade em `backend/tests/property/test_upload_response_prop.py` — Feature: semantic-log-explorer, Property 3: Resposta de upload contém campos obrigatórios
- [x] 7.6 [PBT] Escrever teste de propriedade em `backend/tests/property/test_sse_format_prop.py` — Feature: semantic-log-explorer, Property 9: Resposta de chat utiliza formato SSE

## 8. Configuração do Frontend
- [x] 8.1 Inicializar projeto VueJS 3 em `frontend/` com Vite, Composition API e dependências (markdown-it ou marked para renderização Markdown)
- [x] 8.2 Criar `frontend/src/assets/styles.css` com estilos minimalistas (estilo Shadcn UI)
- [x] 8.3 Configurar `frontend/src/main.js` e `frontend/src/App.vue` com layout principal

## 9. Componentes do Frontend
- [x] 9.1 Criar `frontend/src/components/FileUpload.vue` com upload drag-and-drop, validação de formato (.log, .txt, .json), exibição de progresso e confirmação/erro
- [x] 9.2 Criar `frontend/src/components/ChatWindow.vue` com área de conversa, scroll automático, campo de entrada e estado de loading
- [x] 9.3 Criar `frontend/src/components/MessageBubble.vue` com renderização de mensagens (usuário/IA), suporte a Markdown e blocos de código formatados
- [x] 9.4 Criar `frontend/src/composables/useChat.js` com lógica de comunicação API, consumo de SSE, gerenciamento de estado (mensagens, loading, erro)

## 10. Testes do Frontend
- [ ] 10.1 Escrever testes unitários em `frontend/tests/unit/FileUpload.test.js` para componente de upload
- [ ] 10.2 Escrever testes unitários em `frontend/tests/unit/ChatWindow.test.js` para interface de chat
- [ ] 10.3 Escrever testes unitários em `frontend/tests/unit/MessageBubble.test.js` para renderização de Markdown
- [ ] 10.4 Escrever testes unitários em `frontend/tests/unit/useChat.test.js` para composable de comunicação API

## 11. Configuração de Testes do Backend
- [x] 11.1 Criar `backend/tests/conftest.py` com fixtures compartilhadas (test client async, ChromaDB efêmero de teste, mocks de API externa)
- [x] 11.2 Escrever testes unitários em `backend/tests/unit/test_config.py` para carregamento de configurações e falha sem GOOGLE_API_KEY

## 12. Docker e Integração
- [x] 12.1 Atualizar `Dockerfile` se necessário para incluir dependências de teste e configuração de produção
- [x] 12.2 Atualizar `docker-compose.yml` se necessário para garantir orquestração correta dos serviços com variáveis de ambiente
