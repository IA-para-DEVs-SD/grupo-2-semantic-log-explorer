# PRD — Semantic Log Explorer

## 1. Visão Geral do Produto

O Semantic Log Explorer é uma ferramenta de observabilidade inteligente que utiliza IA Generativa com arquitetura RAG (Retrieval-Augmented Generation) para análise semântica de logs. O objetivo principal é reduzir o tempo de diagnóstico de falhas técnicas (MTTR) através de uma interface conversacional em linguagem natural.

**Contexto:** Sprint de 2 semanas — Curso de IA Generativa (SENAI).

**Público-alvo:**
- Desenvolvedores que precisam diagnosticar falhas rapidamente
- Tech Leads que monitoram padrões de erros recorrentes
- Alunos do SENAI em processo de aprendizado de debugging

---

## 2. Requisitos Funcionais

| ID   | Requisito              | Descrição                                                                                                          | Prioridade |
|------|------------------------|--------------------------------------------------------------------------------------------------------------------|------------|
| RF01 | Ingestão de Logs       | Upload de arquivos de log nos formatos `.log`, `.txt` e `.json`.                                                   | Crítica    |
| RF02 | Vetorização (RAG)      | Processamento dos logs em chunks semânticos e armazenamento em banco de vetores (ChromaDB).                        | Crítica    |
| RF03 | Interface de Chat      | Interface conversacional onde o usuário digita perguntas em linguagem natural sobre os logs ingeridos.              | Crítica    |
| RF04 | Análise de Causa Raiz  | Correlação de erros e sugestão de provável causa raiz baseada no contexto recuperado dos logs.                      | Alta       |
| RF05 | Filtro Temporal        | Restrição da análise a um intervalo de tempo específico contido nos logs.                                          | Média      |
| RF06 | Sugestão de Fix        | Para erros conhecidos (ex: Stack Traces), sugestão de trechos de código ou comandos para correção.                 | Média      |

---

## 3. Requisitos Não-Funcionais

| ID    | Requisito        | Descrição                                                                                                    |
|-------|------------------|--------------------------------------------------------------------------------------------------------------|
| RNF01 | Latência         | Respostas do chat em até 10 segundos, com streaming para manter fluidez.                                     |
| RNF02 | Segurança        | Chaves de API gerenciadas exclusivamente via variáveis de ambiente (`.env`).                                  |
| RNF03 | Privacidade      | Zero Data Retention — banco de vetores efêmero, limpo ao final da sessão. Sanitização de PII via Regex.      |
| RNF04 | Usabilidade      | Interface minimalista focada em produtividade técnica (estilo Shadcn UI).                                    |
| RNF05 | Escalabilidade   | Suporte a arquivos de log de até 50MB no MVP.                                                                |

---

## 4. Histórias de Usuário

### 🔧 Perfil: Desenvolvedor (Foco em Debugging)

**US01 — Diagnóstico de Erro Isolado**
> Como desenvolvedor, eu quero fazer o upload de um arquivo de log específico de uma falha em produção, para que a IA identifique a linha exata e a causa raiz do erro (ex: `NullPointerException`) sem que eu precise ler milhares de linhas manualmente.

- Critério de Aceite: O sistema deve destacar o trecho do log original que originou a falha.

**US02 — Sugestão de Correção (Quick Fix)**
> Como desenvolvedor, eu quero que a IA sugira o comando ou o trecho de código necessário para corrigir o erro encontrado, para que eu reduza o tempo médio de reparo (MTTR) e evite erros de sintaxe na correção.

- Critério de Aceite: A sugestão deve ser formatada em um bloco de código Markdown pronto para copiar.

**US03 — Explicação de Stack Traces Complexos**
> Como desenvolvedor menos experiente, eu quero perguntar o que significa um erro específico de infraestrutura (ex: erro de conexão com banco de dados), para que eu possa aprender sobre a arquitetura do sistema enquanto resolvo o problema.

- Critério de Aceite: A resposta deve ser didática e contextualizada com os logs fornecidos.

---

### 🏗️ Perfil: Tech Lead / SRE (Foco em Padrões e Monitoramento)

**US04 — Análise de Tendências e Recorrência**
> Como Tech Lead, eu quero interrogar o sistema sobre a frequência de um erro específico nas últimas 24 horas, para que eu possa decidir se o problema é um caso isolado ou uma falha sistêmica que exige um hotfix urgente.

- Critério de Aceite: A IA deve correlacionar múltiplos eventos de log que possuem a mesma causa raiz semântica.

**US05 — Onboarding de Sistemas Legados**
> Como líder técnico, eu quero que novos membros da equipe usem o Semantic Log Explorer para interrogar logs de sistemas antigos, para que eles entendam o fluxo de funcionamento do software sem precisar de horas de pareamento técnico.

- Critério de Aceite: O sistema deve ser capaz de explicar o fluxo lógico ("O que aconteceu antes do erro?") com base na sequência de logs.

---

### 🛡️ Perfil: Segurança e Compliance (Foco em RNF)

**US06 — Sanitização de Dados Sensíveis**
> Como responsável pela segurança dos dados, eu quero que o sistema mascare automaticamente informações sensíveis (CPFs, e-mails) antes de enviá-los para a API do Gemini, para que estejamos em conformidade com a LGPD e as políticas de privacidade do SENAI.

- Critério de Aceite: Nenhum dado sensível em texto claro deve ser enviado para o modelo de linguagem (LLM).

**US07 — Sessão de Dados Efêmera**
> Como usuário do sistema, eu quero que os logs e vetores gerados sejam excluídos ao final da minha sessão, para garantir que dados de logs de produção não fiquem armazenados desnecessariamente no servidor da aplicação.

- Critério de Aceite: O banco ChromaDB deve ser limpo ao encerrar o container ou a sessão do usuário.

---

### 🚀 Perfil: Usuário de Negócio / Aluno (Foco em UX)

**US08 — Resumo Executivo de Incidentes**
> Como aluno ou gestor, eu quero pedir um resumo dos erros mais críticos em linguagem natural, para que eu possa reportar o status da aplicação de forma clara em uma reunião de Daily.

- Critério de Aceite: O resumo deve ter no máximo 5 frases e ser direto ao ponto.

**US09 — Aprendizado Contextualizado**
> Como aluno do SENAI, eu quero que a IA explique termos técnicos encontrados nos logs (ex: `Connection refused`, `Deadlock`, `OOM Kill`) de forma didática, para que eu aprenda conceitos de infraestrutura e sistemas enquanto debugo.

- Critério de Aceite: A explicação deve referenciar o trecho do log onde o termo aparece e usar linguagem acessível.

---

## 5. Stack Tecnológica

| Camada             | Tecnologia                                      |
|--------------------|--------------------------------------------------|
| Backend            | Python 3.10+, FastAPI                            |
| IA / Orquestração  | LangChain ou LlamaIndex                          |
| Vector DB          | ChromaDB (local/efêmero para o MVP)              |
| LLM                | Google Gemini 1.5 Pro (fallback: OpenAI GPT-4)   |
| Embeddings         | `text-embedding-004` (Google) — 768 dimensões    |
| Frontend           | VueJS 3 (Composition API)                        |
| Package Managers   | UV (backend), NPM (frontend)                     |
| Containerização    | Docker / Docker Compose                          |

---

## 6. Plano de Testes (MVP)

| Teste                  | Descrição                                                                                                  |
|------------------------|------------------------------------------------------------------------------------------------------------|
| Similaridade Semântica | Pergunta "erro de banco" deve retornar logs contendo `SQLState` ou `Connection refused`.                   |
| Resumo de Logs         | Input de log com 1000 linhas — IA deve resumir o erro em no máximo 5 frases.                               |
| Sugestão de Correção   | Simulação de erro de permissão de pasta — IA deve sugerir o comando `chmod` correto.                       |
| Latência               | Respostas devem ser entregues (início do stream) em menos de 10 segundos.                                  |
| Sanitização de PII     | Logs contendo CPFs, e-mails ou senhas devem ser mascarados antes do envio à API do LLM.                    |

---

## 7. Escopo do MVP vs. Futuro

| Funcionalidade                     | MVP | Futuro |
|------------------------------------|-----|--------|
| Upload de logs (.log, .txt, .json) | ✅  |        |
| Vetorização e busca semântica      | ✅  |        |
| Chat com linguagem natural         | ✅  |        |
| Análise de causa raiz              | ✅  |        |
| Streaming de respostas             | ✅  |        |
| Sanitização de PII                 | ✅  |        |
| Filtro temporal                    |     | ✅     |
| Sugestão de fix                    |     | ✅     |
| Persistência de sessões            |     | ✅     |
| Dashboard de métricas              |     | ✅     |
| Suporte a múltiplos LLMs          |     | ✅     |

---

## 8. Equipe

- Josiel Eliseu Borges
- Luiz Antonio Roussenq
- Arthur Guerra Batista
- Barbara Haydée
- Caio Rodrigo Oliveira
- Caio Batista dos Santos
