# Arquitetura Técnica — Semantic Log Explorer

## 1. Visão Geral

O Semantic Log Explorer opera sobre um pipeline de RAG (Retrieval-Augmented Generation) especializado em dados de observabilidade. A arquitetura é composta por quatro estágios principais: Ingestão, Indexação, Recuperação e Geração.

```
┌─────────────┐     ┌─────────────────┐     ┌───────────┐     ┌─────────────┐
│   Frontend   │────▶│   FastAPI        │────▶│  ChromaDB  │────▶│  Gemini LLM │
│   (VueJS)    │◀────│   (Backend)      │◀────│  (Vetores) │     │  (Resposta) │
└─────────────┘     └─────────────────┘     └───────────┘     └─────────────┘
      Chat UI         Ingestão + RAG         Similaridade        Geração
```

---

## 2. Pipeline de Dados

### 2.1 Ingestão e Pré-processamento

O módulo de ingestão recebe arquivos nos formatos `.log`, `.txt` e `.json` e executa:

1. **Limpeza:** Remoção de ruído — timestamps irrelevantes, IDs de sessão únicos que não agregam valor semântico.
2. **Sanitização de PII:** Aplicação de Regex para mascarar CPFs, e-mails e senhas antes de qualquer envio externo.
3. **Chunking Semântico:** Diferente de textos comuns, os logs são divididos por eventos ou stack traces completos, preservando o contexto do erro intacto.

```
Arquivo de Log (.log/.txt/.json)
        │
        ▼
┌──────────────────┐
│  Limpeza + PII   │
│  Sanitization    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Chunking por    │
│  Evento/Stack    │
└────────┬─────────┘
         │
         ▼
   Chunks prontos
   para vetorização
```

### 2.2 Indexação Vetorial

- **Modelo de Embeddings:** `text-embedding-004` (Google) — vetores de 768 dimensões.
- **Vector Store:** ChromaDB em modo local/efêmero.
- **Metadados por vetor:** `filename`, `timestamp`, `log_level`.

### 2.3 Recuperação (Retrieval)

Quando o usuário faz uma pergunta:

1. A query é convertida em vetor usando o mesmo modelo de embeddings.
2. Busca por similaridade de cosseno no ChromaDB.
3. Retorno dos 5–10 chunks mais relevantes.

### 2.4 Geração de Resposta (Augmented Generation)

O LLM (Gemini 1.5 Pro) recebe os chunks recuperados junto com um prompt de sistema especializado e gera a resposta via streaming.

---

## 3. Componentes do Sistema

### 3.1 Backend (FastAPI)

```
backend/src/
├── main.py              # Entrypoint FastAPI, rotas principais
├── api/
│   ├── routes/
│   │   ├── upload.py    # POST /upload — ingestão de logs
│   │   └── chat.py      # POST /chat — perguntas ao RAG
│   └── dependencies.py  # Injeção de dependências
├── core/
│   ├── config.py        # Configurações e variáveis de ambiente
│   └── security.py      # Sanitização de PII
├── services/
│   ├── ingestion.py     # Limpeza, chunking e pré-processamento
│   ├── vectorstore.py   # Interface com ChromaDB
│   ├── retriever.py     # Busca semântica
│   └── llm.py           # Integração com Gemini / prompt engineering
└── models/
    └── schemas.py       # Pydantic models (request/response)
```

### 3.2 Frontend (VueJS 3)

```
frontend/src/
├── App.vue
├── main.js
├── components/
│   ├── ChatWindow.vue    # Área de conversa com streaming
│   ├── MessageBubble.vue # Renderização de mensagens (Markdown)
│   └── FileUpload.vue    # Upload de arquivos de log
├── composables/
│   └── useChat.js        # Lógica de comunicação com a API
└── assets/
    └── styles.css
```

---

## 4. API — Endpoints Principais

### `POST /api/upload`

Upload e processamento de arquivos de log.

| Campo    | Tipo         | Descrição                          |
|----------|--------------|------------------------------------|
| file     | UploadFile   | Arquivo `.log`, `.txt` ou `.json`  |

**Resposta:** `{ "status": "indexed", "chunks": 142, "filename": "app.log" }`

### `POST /api/chat`

Envio de pergunta ao pipeline RAG.

| Campo    | Tipo   | Descrição                              |
|----------|--------|----------------------------------------|
| question | string | Pergunta em linguagem natural          |

**Resposta:** Streaming SSE com a resposta da IA.

---

## 5. Prompt de Sistema (LLM)

```text
Você é um Engenheiro de SRE Senior especializado em análise de logs.

CONTEXTO:
{logs_recuperados_do_chromadb}

INSTRUÇÕES:
1. Analise os logs acima para responder à pergunta do usuário.
2. Se a causa do erro não estiver explícita nos logs fornecidos,
   diga que não encontrou informações suficientes em vez de inventar.
3. Formate códigos de erro ou comandos de correção em blocos de código Markdown.
4. Use uma linguagem técnica, porém direta.
```

---

## 6. Estratégias de Performance

| Estratégia                | Descrição                                                                 |
|---------------------------|---------------------------------------------------------------------------|
| Streaming (SSE)           | Respostas exibidas em tempo real enquanto o LLM gera tokens (RNF01).      |
| Indexação em Background   | Logs maiores que 10MB são processados de forma assíncrona.                |
| ChromaDB Efêmero          | Banco de vetores limpo ao final da sessão — zero data retention (RNF03).  |
| Chunking por Evento       | Preserva contexto completo de stack traces, evitando cortes semânticos.   |

---

## 7. Segurança e Privacidade

- **Variáveis de ambiente:** Todas as chaves de API são gerenciadas via `.env` (RNF02).
- **Sanitização de PII:** Regex aplicado antes do envio para APIs externas — mascara CPFs, e-mails e senhas (RNF03).
- **Zero Data Retention:** ChromaDB em modo efêmero, sem persistência de logs entre sessões.
- **Sem treinamento com dados:** Uso de APIs Enterprise que não utilizam dados enviados para treinamento de modelos.

---

## 8. Infraestrutura (Docker)

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    volumes: ["./backend/src:/app/src"]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [backend]
```

---

## 9. Decisões Técnicas

| Decisão                          | Justificativa                                                                                  |
|----------------------------------|------------------------------------------------------------------------------------------------|
| ChromaDB (local) vs Pinecone     | Simplicidade para o MVP — sem necessidade de infra cloud. Efêmero por design.                  |
| Gemini 1.5 Pro vs GPT-4         | Janela de contexto generosa (1M tokens), ideal para logs longos. Custo menor no tier gratuito. |
| Chunking por evento vs fixo      | Logs têm estrutura diferente de texto — cortar um stack trace ao meio destrói o contexto.      |
| VueJS vs Streamlit               | Maior controle sobre UX, streaming nativo via SSE, e alinhamento com a stack do curso.         |
| UV vs pip                        | Resolução de dependências mais rápida e reprodutível.                                          |
