# Regras de Git

## Gitflow

- Branch principal: `main`
- Branch de desenvolvimento: `develop`
- Branch de novas funcionalidades: `feature/issue-xxx` (na solicitação de criação de branch para a issue xxx)

O processo de desenvolvimento deve seguir sempre a ortem de feature > develop > main

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
