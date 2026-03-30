# Tarefas de Implementação — Docker e Integração

## Tarefa 1: Dockerfile Multi-Estágio para o Backend

- [x] 1.1 Reescrever `./Dockerfile` com três estágios: `base` (python:3.10-slim, UV, `uv sync`), `test` (herda de base, `uv sync --group test`), `production` (herda de base, copia código-fonte, EXPOSE 8000, CMD uvicorn com 4 workers)
- [x] 1.2 Verificar que o estágio `production` não inclui dependências de teste nem arquivos de desenvolvimento
- [x] 1.3 Validar build do estágio production: `docker build --target production -t sle-backend .`

## Tarefa 2: Dockerfile Dedicado para o Frontend

- [x] 2.1 Criar `./frontend/Dockerfile` com dois estágios: `build` (node:18-alpine, ARG VITE_API_URL, `npm ci`, `npm run build`) e `production` (nginx:alpine, copia assets de build para `/usr/share/nginx/html`, copia nginx.conf, EXPOSE 80)
- [x] 2.2 Criar `./frontend/nginx.conf` com: listen 80, root `/usr/share/nginx/html`, location `/api` com proxy_pass para `http://backend:8000`, try_files com fallback para `/index.html`, headers de proxy (Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto)
- [x] 2.3 Validar build do Frontend: `docker build -t sle-frontend ./frontend`

## Tarefa 3: Docker Compose com Orquestração Completa

- [x] 3.1 Reescrever `./docker-compose.yml` com rede customizada `sle-network` (driver bridge)
- [x] 3.2 Configurar serviço `backend` (perfil prod): build target production, porta 8000:8000, env_file `backend/.env`, health check (curl /health, interval 10s, timeout 5s, retries 3), rede sle-network
- [x] 3.3 Configurar serviço `frontend` (perfil prod): build de `./frontend/Dockerfile`, porta 5173:80, depends_on backend com condition service_healthy, build arg VITE_API_URL, rede sle-network, health check (curl localhost:80, interval 10s, timeout 5s, retries 3)
- [x] 3.4 Configurar serviço `backend-dev` (perfil dev): build target base, porta 8000:8000, volumes `./backend:/app/backend`, comando `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload`, env_file, health check, rede sle-network
- [x] 3.5 Configurar serviço `frontend-dev` (perfil dev): imagem node:18-alpine, porta 5173:5173, volumes `./frontend:/app`, comando `npm run dev -- --host`, depends_on backend-dev com condition service_healthy, rede sle-network, health check (curl localhost:5173, interval 10s, timeout 5s, retries 3)

## Tarefa 4: Gerenciamento de Variáveis de Ambiente

- [x] 4.1 Garantir que o Dockerfile do Backend não contém valores sensíveis hardcoded (sem ENV com chaves de API, sem COPY de .env)
- [x] 4.2 Configurar build arg `VITE_API_URL` no docker-compose.yml para o serviço frontend (prod)
- [x] 4.3 Documentar no README.md a necessidade de criar `backend/.env` a partir de `backend/.env.example` antes de executar docker compose

## Tarefa 5: Testes de Configuração

- [x] 5.1 Criar testes unitários que verificam a estrutura do Dockerfile Backend (3 estágios, imagem base, WORKDIR, EXPOSE)
- [x] 5.2 Criar testes unitários que verificam a estrutura do Dockerfile Frontend (2 estágios, imagens corretas, ARG, EXPOSE)
- [x] 5.3 Criar testes unitários que verificam a estrutura do docker-compose.yml (rede, serviços, health checks, perfis, portas, depends_on)
- [x] 5.4 Criar testes unitários que verificam a configuração nginx.conf (listen 80, proxy /api, SPA fallback, root)
- [x] 5.5 Criar testes baseados em propriedades para Propriedade 1: ausência de valores sensíveis nas instruções Docker (Feature: docker-integration, Property 1)
- [x] 5.6 Criar testes baseados em propriedades para Propriedade 2: proxy reverso Nginx para rotas /api (Feature: docker-integration, Property 2)
- [x] 5.7 Criar testes baseados em propriedades para Propriedade 3: fallback SPA para rotas não-estáticas (Feature: docker-integration, Property 3)
