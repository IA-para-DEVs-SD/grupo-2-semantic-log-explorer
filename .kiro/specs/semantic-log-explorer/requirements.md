# Documento de Requisitos — Semantic Log Explorer

## Introdução

O Semantic Log Explorer é uma ferramenta de observabilidade inteligente que utiliza IA Generativa com arquitetura RAG (Retrieval-Augmented Generation) para análise semântica de logs. A aplicação permite que desenvolvedores façam upload de arquivos de log e interroguem o sistema em linguagem natural para diagnosticar falhas, identificar causas raiz e obter sugestões de correção, reduzindo o MTTR (Mean Time To Repair). O sistema é composto por um backend Python/FastAPI com pipeline RAG (ChromaDB + Google Gemini) e um frontend VueJS 3.

## Glossário

- **Sistema**: A aplicação Semantic Log Explorer como um todo (backend + frontend)
- **Backend**: Servidor FastAPI responsável pela API REST, pipeline RAG e integração com LLM
- **Frontend**: Aplicação VueJS 3 que fornece a interface de chat e upload de arquivos
- **Pipeline_RAG**: Pipeline de Retrieval-Augmented Generation composto por ingestão, vetorização, recuperação semântica e geração de resposta
- **Módulo_de_Ingestão**: Componente do backend responsável por limpeza, sanitização e chunking dos logs
- **Módulo_de_Sanitização**: Componente do backend responsável por mascarar dados sensíveis (PII) via Regex
- **VectorStore**: Interface com o ChromaDB para armazenamento e busca de vetores de embeddings
- **Retriever**: Componente responsável pela busca semântica por similaridade de cosseno no ChromaDB
- **Serviço_LLM**: Componente responsável pela integração com Google Gemini 1.5 Pro e prompt engineering
- **ChromaDB**: Banco de dados vetorial local e efêmero utilizado para armazenar embeddings dos logs
- **Gemini**: Google Gemini 1.5 Pro, modelo de linguagem utilizado para geração de respostas
- **Embeddings**: Representações vetoriais de 768 dimensões geradas pelo modelo text-embedding-004 (Google)
- **Chunk**: Fragmento semântico de um log, dividido por evento ou stack trace completo
- **PII**: Informação Pessoal Identificável (CPFs, e-mails, senhas)
- **SSE**: Server-Sent Events, protocolo utilizado para streaming de respostas
- **Sessão**: Período de uso do sistema por um usuário, do início ao encerramento do container ou navegação

## Requisitos

### Requisito 1: Ingestão de Arquivos de Log

**User Story:** Como desenvolvedor, eu quero fazer upload de arquivos de log nos formatos .log, .txt e .json, para que o sistema processe e indexe o conteúdo para análise semântica.

#### Critérios de Aceite

1. WHEN o usuário envia um arquivo via POST /api/upload, THE Backend SHALL aceitar arquivos nos formatos .log, .txt e .json
2. IF o usuário enviar um arquivo com formato diferente de .log, .txt ou .json, THEN THE Backend SHALL retornar um erro HTTP 400 com mensagem descritiva do formato inválido
3. IF o usuário enviar um arquivo com tamanho superior a 50MB, THEN THE Backend SHALL retornar um erro HTTP 413 com mensagem indicando o limite de tamanho
4. WHEN um arquivo válido é recebido, THE Módulo_de_Ingestão SHALL executar limpeza, sanitização de PII e chunking semântico do conteúdo
5. WHEN o processamento do arquivo é concluído, THE Backend SHALL retornar uma resposta JSON contendo status "indexed", quantidade de chunks gerados e nome do arquivo
6. WHEN um arquivo válido é recebido, THE Módulo_de_Ingestão SHALL dividir o conteúdo em chunks preservando eventos e stack traces completos sem cortar o contexto semântico

### Requisito 2: Vetorização e Indexação no ChromaDB

**User Story:** Como desenvolvedor, eu quero que os logs processados sejam convertidos em vetores e armazenados no ChromaDB, para que o sistema consiga realizar buscas semânticas sobre o conteúdo.

#### Critérios de Aceite

1. WHEN os chunks de log são gerados pelo Módulo_de_Ingestão, THE VectorStore SHALL gerar embeddings de 768 dimensões utilizando o modelo text-embedding-004 do Google
2. WHEN os embeddings são gerados, THE VectorStore SHALL armazenar cada vetor no ChromaDB com os metadados filename, timestamp e log_level
3. THE VectorStore SHALL operar o ChromaDB em modo local e efêmero sem persistência em disco entre sessões

### Requisito 3: Interface de Chat com Linguagem Natural

**User Story:** Como desenvolvedor, eu quero interagir com o sistema através de uma interface de chat em linguagem natural, para que eu possa fazer perguntas sobre os logs sem precisar ler milhares de linhas manualmente.

#### Critérios de Aceite

1. THE Frontend SHALL exibir uma interface de chat com área de conversa (ChatWindow), bolhas de mensagem (MessageBubble) e campo de entrada de texto
2. WHEN o usuário envia uma pergunta, THE Frontend SHALL transmitir a pergunta via POST /api/chat para o Backend
3. WHEN o Backend recebe uma pergunta via POST /api/chat, THE Retriever SHALL converter a pergunta em vetor e buscar os 5 a 10 chunks mais relevantes por similaridade de cosseno no ChromaDB
4. WHEN os chunks relevantes são recuperados, THE Serviço_LLM SHALL enviar os chunks junto com o prompt de sistema especializado para o Gemini e retornar a resposta via streaming SSE
5. WHEN a resposta SSE é recebida, THE Frontend SHALL renderizar os tokens em tempo real na interface de chat
6. THE Frontend SHALL renderizar blocos de código Markdown nas respostas do Serviço_LLM com formatação adequada

### Requisito 4: Diagnóstico de Erro e Análise de Causa Raiz

**User Story:** Como desenvolvedor, eu quero que a IA identifique a linha exata e a causa raiz de erros nos logs, para que eu diagnostique falhas rapidamente sem leitura manual.

#### Critérios de Aceite

1. WHEN o usuário pergunta sobre um erro específico, THE Serviço_LLM SHALL identificar e destacar o trecho do log original que originou a falha na resposta
2. WHEN múltiplos eventos de log possuem a mesma causa raiz semântica, THE Serviço_LLM SHALL correlacionar os eventos e apresentar a análise de causa raiz unificada
3. IF o Serviço_LLM não encontrar informações suficientes nos logs recuperados para determinar a causa raiz, THEN THE Serviço_LLM SHALL informar explicitamente que não encontrou dados suficientes em vez de gerar uma resposta especulativa

### Requisito 5: Explicação Didática de Stack Traces e Termos Técnicos

**User Story:** Como desenvolvedor menos experiente, eu quero que a IA explique stack traces complexos e termos técnicos dos logs de forma didática, para que eu aprenda sobre a arquitetura do sistema enquanto resolvo problemas.

#### Critérios de Aceite

1. WHEN o usuário pergunta sobre o significado de um erro de infraestrutura, THE Serviço_LLM SHALL fornecer uma explicação didática e contextualizada com os logs fornecidos
2. WHEN o usuário pergunta sobre termos técnicos encontrados nos logs (ex: Connection refused, Deadlock, OOM Kill), THE Serviço_LLM SHALL referenciar o trecho do log onde o termo aparece e utilizar linguagem acessível na explicação
3. WHEN o usuário pergunta sobre o fluxo de eventos que precedeu um erro, THE Serviço_LLM SHALL explicar a sequência lógica de eventos com base na ordem dos logs recuperados

### Requisito 6: Resumo Executivo de Incidentes

**User Story:** Como gestor ou aluno, eu quero pedir um resumo dos erros mais críticos em linguagem natural, para que eu possa reportar o status da aplicação de forma clara.

#### Critérios de Aceite

1. WHEN o usuário solicita um resumo dos erros, THE Serviço_LLM SHALL gerar um resumo executivo contendo no máximo 5 frases diretas sobre os erros mais críticos encontrados nos logs
2. THE Serviço_LLM SHALL utilizar linguagem natural clara e direta no resumo executivo, adequada para comunicação em reuniões

### Requisito 7: Sanitização de Dados Sensíveis (PII)

**User Story:** Como responsável pela segurança dos dados, eu quero que o sistema mascare automaticamente informações sensíveis antes de enviá-las para a API do Gemini, para conformidade com a LGPD.

#### Critérios de Aceite

1. WHEN o Módulo_de_Ingestão processa um arquivo de log, THE Módulo_de_Sanitização SHALL mascarar CPFs, e-mails e senhas utilizando expressões regulares antes de qualquer processamento adicional
2. THE Módulo_de_Sanitização SHALL executar a sanitização antes do envio de qualquer texto para o modelo de embeddings ou para o Gemini
3. IF um chunk de log contiver dados sensíveis após a sanitização, THEN THE Módulo_de_Sanitização SHALL substituir os dados por marcadores genéricos (ex: [CPF_MASCARADO], [EMAIL_MASCARADO], [SENHA_MASCARADA])
4. THE Backend SHALL garantir que nenhum dado sensível em texto claro seja enviado para APIs externas (Gemini, text-embedding-004)

### Requisito 8: Sessão de Dados Efêmera

**User Story:** Como usuário do sistema, eu quero que os logs e vetores gerados sejam excluídos ao final da minha sessão, para garantir que dados de produção não fiquem armazenados no servidor.

#### Critérios de Aceite

1. THE VectorStore SHALL operar o ChromaDB em modo efêmero, sem persistência de dados em disco
2. WHEN o container do Backend é encerrado, THE VectorStore SHALL garantir que todos os vetores e metadados armazenados no ChromaDB sejam descartados
3. WHEN a sessão do usuário é encerrada, THE Backend SHALL limpar a coleção correspondente no ChromaDB

### Requisito 9: Streaming de Respostas com Baixa Latência

**User Story:** Como desenvolvedor, eu quero que as respostas do chat sejam entregues via streaming em tempo real, para que eu tenha uma experiência fluida sem esperar longos tempos de carregamento.

#### Critérios de Aceite

1. WHEN o Serviço_LLM gera uma resposta, THE Backend SHALL transmitir os tokens via Server-Sent Events (SSE) para o Frontend
2. THE Backend SHALL iniciar o streaming da resposta em menos de 10 segundos após o recebimento da pergunta
3. WHILE o streaming está em andamento, THE Frontend SHALL exibir os tokens recebidos progressivamente na interface de chat

### Requisito 10: Configuração Segura de Chaves de API

**User Story:** Como desenvolvedor, eu quero que as chaves de API sejam gerenciadas via variáveis de ambiente, para que credenciais sensíveis não sejam expostas no código-fonte.

#### Critérios de Aceite

1. THE Backend SHALL carregar a chave GOOGLE_API_KEY exclusivamente a partir de variáveis de ambiente definidas no arquivo .env
2. IF a variável GOOGLE_API_KEY não estiver definida no ambiente, THEN THE Backend SHALL falhar na inicialização com uma mensagem de erro descritiva
3. THE Backend SHALL fornecer um arquivo .env.example documentando todas as variáveis de ambiente necessárias sem conter valores reais

### Requisito 11: Upload de Arquivos no Frontend

**User Story:** Como desenvolvedor, eu quero fazer upload de arquivos de log diretamente pela interface web, para que eu possa iniciar a análise sem precisar usar ferramentas de linha de comando.

#### Critérios de Aceite

1. THE Frontend SHALL exibir um componente de upload (FileUpload) que aceite arquivos nos formatos .log, .txt e .json
2. WHEN o usuário seleciona um arquivo, THE Frontend SHALL enviar o arquivo via POST /api/upload para o Backend
3. WHEN o upload é concluído com sucesso, THE Frontend SHALL exibir uma confirmação com o nome do arquivo e a quantidade de chunks indexados
4. IF o upload falhar, THEN THE Frontend SHALL exibir uma mensagem de erro descritiva para o usuário

### Requisito 12: Prompt de Sistema Especializado

**User Story:** Como desenvolvedor, eu quero que o LLM utilize um prompt de sistema especializado em análise de logs, para que as respostas sejam técnicas, precisas e contextualizadas.

#### Critérios de Aceite

1. THE Serviço_LLM SHALL utilizar um prompt de sistema que instrua o Gemini a atuar como Engenheiro de SRE Senior especializado em análise de logs
2. THE Serviço_LLM SHALL incluir os chunks recuperados do ChromaDB como contexto no prompt enviado ao Gemini
3. THE Serviço_LLM SHALL instruir o Gemini a formatar códigos de erro e comandos de correção em blocos de código Markdown
4. THE Serviço_LLM SHALL instruir o Gemini a informar quando não encontrar informações suficientes nos logs em vez de gerar respostas especulativas

### Requisito 13: Containerização com Docker

**User Story:** Como desenvolvedor, eu quero executar toda a aplicação via Docker Compose, para que o ambiente de desenvolvimento seja reprodutível e fácil de configurar.

#### Critérios de Aceite

1. THE Sistema SHALL fornecer um Dockerfile para o Backend que utilize Python 3.10 e UV como gerenciador de pacotes
2. THE Sistema SHALL fornecer um docker-compose.yml que orquestre os serviços de Backend (porta 8000) e Frontend (porta 5173)
3. WHEN o comando docker-compose up --build é executado, THE Sistema SHALL iniciar ambos os serviços com as variáveis de ambiente carregadas do arquivo .env
