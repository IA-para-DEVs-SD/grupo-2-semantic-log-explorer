# Documento de Requisitos — Docker e Integração

## Introdução

Este documento define os requisitos para a melhoria da configuração Docker do projeto Semantic Log Explorer. O objetivo é tornar o ambiente containerizado pronto para produção, com builds multi-estágio, Dockerfiles dedicados para cada serviço, health checks, gerenciamento adequado de variáveis de ambiente e suporte a configurações distintas para desenvolvimento e produção.

Atualmente, o projeto possui um Dockerfile básico para o backend (sem multi-stage build, sem dependências de teste) e o frontend roda diretamente a partir de uma imagem Node genérica com `npm install` executado a cada inicialização do container. A orquestração via `docker-compose.yml` não possui health checks, rede dedicada nem separação entre perfis de desenvolvimento e produção.

## Glossário

- **Backend**: Serviço FastAPI (Python 3.10+) que expõe a API REST do Semantic Log Explorer, incluindo endpoints de upload e chat.
- **Frontend**: Aplicação VueJS 3 servida pelo Vite em desenvolvimento e por servidor estático (Nginx) em produção.
- **Docker_Compose**: Ferramenta de orquestração que define e gerencia os serviços containerizados do projeto.
- **Dockerfile_Backend**: Arquivo de definição de imagem Docker para o serviço Backend.
- **Dockerfile_Frontend**: Arquivo de definição de imagem Docker para o serviço Frontend.
- **Health_Check**: Verificação periódica de saúde de um serviço containerizado para garantir que está operacional.
- **Multi_Stage_Build**: Técnica de construção de imagens Docker que utiliza múltiplos estágios para separar dependências de build das de runtime, reduzindo o tamanho final da imagem.
- **UV**: Gerenciador de pacotes Python utilizado no Backend para resolução rápida de dependências.
- **Perfil_Dev**: Configuração Docker otimizada para desenvolvimento local, com hot-reload e volumes montados.
- **Perfil_Prod**: Configuração Docker otimizada para produção, com imagens mínimas e assets pré-compilados.

## Requisitos

### Requisito 1: Dockerfile Multi-Estágio para o Backend

**User Story:** Como desenvolvedor, eu quero que o Dockerfile do Backend utilize multi-stage build, para que a imagem de produção seja mínima e as dependências de teste fiquem disponíveis apenas no estágio de teste.

#### Critérios de Aceitação

1. THE Dockerfile_Backend SHALL utilizar multi-stage build com pelo menos três estágios: base (dependências de runtime), test (dependências de teste) e production (imagem final mínima)
2. WHEN o estágio base é construído, THE Dockerfile_Backend SHALL instalar o UV e executar `uv sync` para resolver as dependências de runtime do projeto
3. WHEN o estágio test é construído, THE Dockerfile_Backend SHALL instalar as dependências do grupo opcional `test` definidas em `pyproject.toml`
4. WHEN o estágio production é construído, THE Dockerfile_Backend SHALL copiar apenas os artefatos necessários para execução, excluindo dependências de teste e arquivos de desenvolvimento
5. THE Dockerfile_Backend SHALL utilizar `python:3.10-slim` como imagem base para manter o tamanho reduzido
6. THE Dockerfile_Backend SHALL definir o `WORKDIR` como `/app`
7. THE Dockerfile_Backend SHALL expor a porta 8000

### Requisito 2: Dockerfile Dedicado para o Frontend

**User Story:** Como desenvolvedor, eu quero que o Frontend tenha um Dockerfile dedicado com multi-stage build, para que a imagem de produção sirva assets estáticos pré-compilados via Nginx em vez de executar `npm install` a cada inicialização.

#### Critérios de Aceitação

1. THE Dockerfile_Frontend SHALL utilizar multi-stage build com pelo menos dois estágios: build (compilação dos assets) e production (servidor estático)
2. WHEN o estágio build é construído, THE Dockerfile_Frontend SHALL utilizar uma imagem `node:18-alpine` para executar `npm ci` e `npm run build`
3. WHEN o estágio production é construído, THE Dockerfile_Frontend SHALL utilizar uma imagem `nginx:alpine` para servir os assets estáticos gerados pelo Vite
4. THE Dockerfile_Frontend SHALL copiar uma configuração Nginx que faça proxy reverso das requisições `/api` para o serviço Backend
5. THE Dockerfile_Frontend SHALL expor a porta 80
6. WHEN a variável `VITE_API_URL` é fornecida durante o build, THE Dockerfile_Frontend SHALL utilizá-la como argumento de build (`ARG`) para configurar a URL da API

### Requisito 3: Orquestração de Serviços com Docker Compose

**User Story:** Como desenvolvedor, eu quero que o `docker-compose.yml` orquestre corretamente os serviços Backend e Frontend com rede dedicada e dependências explícitas, para que a comunicação entre serviços seja confiável.

#### Critérios de Aceitação

1. THE Docker_Compose SHALL definir uma rede customizada do tipo bridge para comunicação entre os serviços Backend e Frontend
2. THE Docker_Compose SHALL configurar o serviço Backend com build a partir do Dockerfile_Backend localizado no diretório raiz
3. THE Docker_Compose SHALL configurar o serviço Frontend com build a partir do Dockerfile_Frontend localizado no diretório `frontend/`
4. THE Docker_Compose SHALL definir que o serviço Frontend depende do serviço Backend estar saudável (`depends_on` com condição `service_healthy`)
5. THE Docker_Compose SHALL mapear a porta 8000 do Backend para a porta 8000 do host
6. THE Docker_Compose SHALL mapear a porta 80 do Frontend para a porta 5173 do host em produção

### Requisito 4: Health Checks dos Serviços

**User Story:** Como desenvolvedor, eu quero que os serviços Docker possuam health checks configurados, para que o Docker Compose possa verificar se cada serviço está operacional antes de iniciar serviços dependentes.

#### Critérios de Aceitação

1. THE Docker_Compose SHALL configurar um health check para o serviço Backend que faça requisição HTTP ao endpoint `GET /health`
2. WHEN o health check do Backend é executado, THE Docker_Compose SHALL utilizar intervalo de 10 segundos, timeout de 5 segundos e limite de 3 tentativas
3. THE Docker_Compose SHALL configurar um health check para o serviço Frontend que verifique a disponibilidade do servidor Nginx
4. WHEN o health check do Frontend é executado, THE Docker_Compose SHALL utilizar intervalo de 10 segundos, timeout de 5 segundos e limite de 3 tentativas

### Requisito 5: Gerenciamento de Variáveis de Ambiente

**User Story:** Como desenvolvedor, eu quero que as variáveis de ambiente sejam gerenciadas de forma segura e consistente entre os serviços, para que chaves de API e configurações sensíveis não sejam expostas nas imagens Docker.

#### Critérios de Aceitação

1. THE Docker_Compose SHALL carregar as variáveis de ambiente do Backend a partir do arquivo `backend/.env` usando a diretiva `env_file`
2. THE Docker_Compose SHALL passar a variável `VITE_API_URL` para o Frontend como argumento de build
3. THE Dockerfile_Backend SHALL utilizar variáveis de ambiente em tempo de execução, sem incorporar valores sensíveis na imagem
4. IF o arquivo `backend/.env` não existir, THEN THE Docker_Compose SHALL falhar com mensagem clara indicando a necessidade de criar o arquivo a partir de `backend/.env.example`

### Requisito 6: Perfis de Desenvolvimento e Produção

**User Story:** Como desenvolvedor, eu quero ter configurações Docker separadas para desenvolvimento e produção, para que eu possa usar hot-reload durante o desenvolvimento e imagens otimizadas em produção.

#### Critérios de Aceitação

1. THE Docker_Compose SHALL suportar perfis (`profiles`) para separar configurações de desenvolvimento e produção
2. WHILE o perfil de desenvolvimento está ativo, THE Docker_Compose SHALL montar volumes locais (`./backend:/app/backend` e `./frontend:/app`) para permitir hot-reload
3. WHILE o perfil de desenvolvimento está ativo, THE Docker_Compose SHALL utilizar o comando de desenvolvimento do Vite (`npm run dev -- --host`) para o Frontend em vez do Nginx
4. WHILE o perfil de produção está ativo, THE Docker_Compose SHALL utilizar as imagens multi-stage otimizadas sem volumes montados
5. WHILE o perfil de desenvolvimento está ativo, THE Docker_Compose SHALL utilizar o comando `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload` para o Backend
6. WHILE o perfil de produção está ativo, THE Docker_Compose SHALL utilizar o comando `uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4` para o Backend

### Requisito 7: Configuração Nginx para o Frontend em Produção

**User Story:** Como desenvolvedor, eu quero que o Frontend em produção utilize Nginx com proxy reverso para a API, para que todas as requisições `/api` sejam encaminhadas ao Backend sem necessidade de CORS.

#### Critérios de Aceitação

1. THE Dockerfile_Frontend SHALL incluir um arquivo de configuração Nginx (`nginx.conf`) que sirva os assets estáticos do diretório `/usr/share/nginx/html`
2. WHEN uma requisição com prefixo `/api` é recebida, THE Dockerfile_Frontend SHALL configurar o Nginx para encaminhar a requisição ao serviço Backend na porta 8000 via proxy reverso
3. WHEN uma rota do frontend não corresponde a um arquivo estático, THE Dockerfile_Frontend SHALL configurar o Nginx para retornar `index.html` (suporte a SPA com Vue Router)
4. THE Dockerfile_Frontend SHALL configurar o Nginx para escutar na porta 80
