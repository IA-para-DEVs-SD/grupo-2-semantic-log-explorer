# Regras de Git

## Gitflow

- Branch principal: `main`
- Branch de desenvolvimento: `develop`
- Branch de novas funcionalidades: `feature/issue-xxx` (na solicitação de criação de branch para a issue xxx)

O processo de desenvolvimento deve seguir sempre a ortem de feature > develop > main

## Criação de branch a partir de uma Issue

As branches criadas a partir de uma issue do board deve:

- Criar a partir da branch develop
- Ter o nome no formato `feature/issue-xxx`. Onde xxx é o número da issue no GitHub (ex: feature/issue-17 para a issue #17)
- Atualizar o responsavel (Assignees) para a pessoa que solicitou a criação da feature
- Deve trocar o status para "Em andamento"

## Publicação da branch

Ao ser solicitado pela publicação da feature, e essa for uma cujo formato é `feature/issue-xxx`, deve ser feito o seguinte:

Commite todos arquivos 
Publique a branch `feature/issue-xxx`
Atualize a develop com a branch `feature/issue-xxx`
Feche essa branch `feature/issue-xxx`
Atualize o status no Board para "Concluído"

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
