# 🤖 Semantic Log Explorer

Ferramenta de observabilidade inteligente que utiliza IA Generativa com arquitetura RAG (Retrieval-Augmented Generation) para análise semântica de logs. Permite que desenvolvedores diagnostiquem falhas em sistemas complexos através de uma interface de chat em linguagem natural, reduzindo o MTTR (Mean Time To Repair).

Projeto desenvolvido durante o curso de Inteligência Artificial Generativa — SENAI.

## 📚 Sumário de Documentações

- [PRD — Product Requirements Document](backend/docs/prd.md)
- [Arquitetura](backend/docs/arquitetura.md)
- [Diagramas UML](backend/docs/diagrama.md)

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.10+, FastAPI |
| IA / Orquestração | LangChain / LlamaIndex |
| Base de Dados Vetorial | ChromaDB |
| LLM | Google Gemini API |
| Embeddings | `text-embedding-004` (Google) |
| Frontend | VueJS 3 (Composition API) |
| Package Managers | UV (backend), NPM (frontend) |
| Linter / Formatter | Ruff |
| Containerização | Docker / Docker Compose |

## 📦 Instruções de Instalação / Uso

### Pré-requisitos

- Python 3.10+
- [UV](https://docs.astral.sh/uv/)
- Node.js e NPM
- Docker e Docker Compose (opcional)

### Instalação

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/semantic-log-explorer.git
cd semantic-log-explorer
```

2. Configure as variáveis de ambiente:

```bash
cp backend/.env.example backend/.env
```

Preencha o arquivo `.env` com suas chaves:

```
GOOGLE_API_KEY=sua_chave_aqui
DATABASE_URL=seu_link_db
```

3. Inicie o backend:

```bash
cd backend
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. Inicie o frontend:

```bash
cd frontend
npm install
npm run dev
```

### Linter / Formatter (Ruff)

O projeto usa [Ruff](https://docs.astral.sh/ruff/) para linting e formatação do código Python. Para rodar manualmente:

```bash
ruff check --fix backend/
ruff format backend/
```

Um hook Kiro executa esses comandos automaticamente ao salvar arquivos `.py`.

### Execução com Docker

1. Crie o arquivo de variáveis de ambiente a partir do template:

```bash
cp backend/.env.example backend/.env
```

Edite `backend/.env` e preencha a variável obrigatória `GOOGLE_API_KEY`. As demais variáveis possuem valores padrão.

2. Execute com o perfil desejado:

**Produção** (imagens otimizadas com Nginx):

```bash
docker compose --profile prod up --build
```

**Desenvolvimento** (hot-reload com volumes montados):

```bash
docker compose --profile dev up --build
```

## 👥 Integrantes do Grupo

- Josiel Eliseu Borges
- Luiz Antonio Roussenq
- Arthur Guerra Batista
- Barbara Haydée
- Caio Rodrigo Oliveira
- Caio Batista dos Santos
