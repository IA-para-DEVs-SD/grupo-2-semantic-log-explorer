---
inclusion: always
---

# Semantic Log Explorer

Ferramenta de observabilidade inteligente com IA Generativa e arquitetura RAG para análise semântica de logs.

## Stack

- Backend: Python 3.10+, FastAPI, LangChain/LlamaIndex, ChromaDB, Google Gemini API
- Frontend: VueJS
- Package Managers: UV (backend), NPM (frontend)

## Linter / Formatter

- Ruff é usado para linting e formatação do código Python
- Um hook Kiro (`ruff-lint-format.kiro.hook`) executa `ruff check --fix` e `ruff format` automaticamente ao salvar arquivos `.py`
- Antes de commitar, garanta que o código passa em `ruff check` e `ruff format --check`

## Convenções

- Código em inglês, documentação em português
- Backend segue padrões FastAPI com tipagem Python
- Frontend segue convenções VueJS 3 com Composition API
