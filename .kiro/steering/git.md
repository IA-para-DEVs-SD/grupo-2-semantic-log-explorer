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

1. Commite todos arquivos na branch `feature/issue-xxx`
2. Publique (push) a branch `feature/issue-xxx` no remote
3. Crie um pull request de `feature/issue-xxx` → `develop`

**Nota**: Os PRs devem ser de `feature/issue-xxx` → `develop` (e não de `develop` → `main`) porque o GitHub não permite ter dois PRs abertos com o mesmo par de branches. Se duas tasks criassem PRs de `develop` → `main` ao mesmo tempo, o segundo PR não poderia ser criado.

## Release (develop → main)

- O merge de `develop` → `main` é feito pelo líder do grupo via PR de release

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

## Pull Request

- Todo PR deve seguir o template definido em `.github/PULL_REQUEST_TEMPLATE.md`
- O corpo do PR deve preencher todas as seções do template: Descrição, Issue Relacionada, Tipo de Mudança, O que foi feito, Testes e Checklist
- Sempre vincular a issue relacionada usando `Closes #XX` para que a issue seja fechada automaticamente ao mergear
- O título do PR deve seguir o formato de commit semântico: `tipo: breve descrição`
