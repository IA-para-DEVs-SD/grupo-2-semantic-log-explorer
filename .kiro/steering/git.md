# Regras de Git

## Gitflow

- Branch principal: `main`
- Branch de desenvolvimento: `develop`
- Branch de novas funcionalidades: `feature/issue-xxx` (na solicitação de criação de branch para a issue xxx)

O processo de desenvolvimento deve seguir sempre a ortem de feature > develop > main

## Criação de branch a partir de uma Issue

As branches criadas a partir de uma issue do board deve:

- Ter o nome no formato `feature/issue-xxx`
- Atualizar o responsavel (Assignees) para a pessoa que solicitou a criação da feature
- Deve trocar o status para "Em andamento"

## Commit Semântico

Formato:

```
tipo: breve descrição

descrição mais detalhada (opcional)
```

Tipos permitidos:

- `feat`: Nova funcionalidade
- `docs`: Documentações
- `fix`: Correções
- `refactor`: Refatorações
- `tests`: Testes unitários, etc
