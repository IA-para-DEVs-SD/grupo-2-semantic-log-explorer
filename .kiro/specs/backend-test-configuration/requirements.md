# Documento de Requisitos — Configuração de Testes do Backend

## Introdução

O backend do Semantic Log Explorer já possui testes unitários (em `backend/tests/unit/`) e testes baseados em propriedades (em `backend/tests/property/`), porém carece de infraestrutura de configuração de testes adequada. Atualmente não existe `pyproject.toml` com configuração do pytest, não há `conftest.py` com fixtures compartilhadas, não há configuração de cobertura de código, e não existe pipeline de CI para execução automatizada dos testes.

Esta feature visa estabelecer a infraestrutura de configuração de testes do backend, garantindo que os testes existentes possam ser executados de forma padronizada, com cobertura medida, fixtures reutilizáveis e integração contínua.

## Glossário

- **Sistema_de_Testes**: Infraestrutura de configuração e execução de testes do backend, incluindo pytest, plugins e arquivos de configuração
- **Pytest**: Framework de testes utilizado pelo projeto Python
- **Conftest**: Arquivo `conftest.py` do pytest que contém fixtures e hooks compartilhados entre os testes
- **Cobertura**: Medição de cobertura de código (code coverage) via pytest-cov
- **Pipeline_CI**: Pipeline de integração contínua no GitHub Actions que executa os testes automaticamente
- **Fixture**: Função do pytest que fornece dados ou objetos reutilizáveis para os testes
- **Marcador**: Decorator do pytest (`@pytest.mark`) que categoriza testes para execução seletiva
- **UV**: Gerenciador de pacotes Python utilizado pelo projeto

## Requisitos

### Requisito 1: Configuração do Pytest no pyproject.toml

**User Story:** Como desenvolvedor, eu quero ter uma configuração centralizada do pytest no `pyproject.toml`, para que todos os testes sejam executados com as mesmas opções padrão sem precisar passar flags manualmente.

#### Critérios de Aceitação

1. THE Sistema_de_Testes SHALL definir a configuração do pytest na seção `[tool.pytest.ini_options]` do arquivo `backend/pyproject.toml`
2. THE Sistema_de_Testes SHALL configurar o diretório de testes como `tests/`
3. THE Sistema_de_Testes SHALL configurar o padrão de descoberta de arquivos de teste como `test_*.py`
4. THE Sistema_de_Testes SHALL configurar o modo de saída verboso (`-v`) como padrão
5. THE Sistema_de_Testes SHALL registrar marcadores customizados para `unit`, `property` e `integration` na configuração do pytest
6. WHEN o comando `pytest` é executado sem argumentos dentro do diretório `backend/`, THE Sistema_de_Testes SHALL descobrir e executar todos os testes nos subdiretórios `tests/unit/` e `tests/property/`
7. THE Sistema_de_Testes SHALL configurar o modo `asyncio_mode = "auto"` para suporte a testes assíncronos

### Requisito 2: Fixtures Compartilhadas via conftest.py

**User Story:** Como desenvolvedor, eu quero ter fixtures compartilhadas em um `conftest.py` raiz, para que eu possa reutilizar objetos comuns (como Settings mockadas e clientes de teste) sem duplicar código entre os módulos de teste.

#### Critérios de Aceitação

1. THE Sistema_de_Testes SHALL fornecer um arquivo `conftest.py` no diretório `backend/tests/`
2. THE Sistema_de_Testes SHALL fornecer uma fixture `mock_settings` que retorne uma instância de `Settings` com valores de teste válidos
3. THE Sistema_de_Testes SHALL fornecer uma fixture `test_app` que retorne uma instância de `FastAPI` configurada com rotas e dependências mockadas
4. THE Sistema_de_Testes SHALL fornecer uma fixture `client` que retorne um `TestClient` sincronizado para testes de rotas HTTP
5. THE Sistema_de_Testes SHALL fornecer uma fixture `async_client` que retorne um `AsyncClient` para testes assíncronos de rotas HTTP
6. WHEN uma fixture do `conftest.py` raiz é utilizada em um teste, THE Sistema_de_Testes SHALL disponibilizar a fixture automaticamente sem necessidade de import explícito
7. THE Sistema_de_Testes SHALL garantir que as fixtures do `conftest.py` raiz sejam compatíveis com os testes existentes em `tests/unit/` e `tests/property/`

### Requisito 3: Configuração de Cobertura de Código

**User Story:** Como desenvolvedor, eu quero medir a cobertura de código dos testes, para que eu possa identificar áreas do código sem cobertura e manter a qualidade do projeto.

#### Critérios de Aceitação

1. THE Sistema_de_Testes SHALL configurar o plugin `pytest-cov` na seção `[tool.coverage]` do `backend/pyproject.toml`
2. THE Sistema_de_Testes SHALL definir o diretório `src/` como alvo de medição de cobertura
3. THE Sistema_de_Testes SHALL excluir os diretórios `tests/`, `__pycache__/` e `.venv/` da medição de cobertura
4. THE Sistema_de_Testes SHALL configurar a geração de relatório de cobertura nos formatos `term-missing` (terminal) e `html` (relatório visual)
5. THE Sistema_de_Testes SHALL excluir linhas com `if __name__ == "__main__"`, `pass`, `...` e `pragma: no cover` da contagem de cobertura
6. THE Sistema_de_Testes SHALL adicionar o diretório de relatório HTML (`htmlcov/`) ao `.gitignore` do backend
7. WHEN o comando `pytest --cov` é executado, THE Sistema_de_Testes SHALL gerar um relatório de cobertura mostrando a porcentagem de linhas cobertas por arquivo

### Requisito 4: Marcadores de Teste para Execução Seletiva

**User Story:** Como desenvolvedor, eu quero poder executar apenas testes unitários ou apenas testes de propriedade separadamente, para que eu possa ter feedback rápido durante o desenvolvimento sem executar a suíte completa.

#### Critérios de Aceitação

1. THE Sistema_de_Testes SHALL aplicar automaticamente o marcador `unit` a todos os testes no diretório `tests/unit/` via `conftest.py`
2. THE Sistema_de_Testes SHALL aplicar automaticamente o marcador `property` a todos os testes no diretório `tests/property/` via `conftest.py`
3. WHEN o comando `pytest -m unit` é executado, THE Sistema_de_Testes SHALL executar apenas os testes do diretório `tests/unit/`
4. WHEN o comando `pytest -m property` é executado, THE Sistema_de_Testes SHALL executar apenas os testes do diretório `tests/property/`
5. WHEN o comando `pytest -m "not property"` é executado, THE Sistema_de_Testes SHALL excluir os testes de propriedade da execução
6. THE Sistema_de_Testes SHALL registrar os marcadores `unit`, `property` e `integration` na configuração do pytest para evitar warnings de marcadores desconhecidos

### Requisito 5: Dependências de Teste no pyproject.toml

**User Story:** Como desenvolvedor, eu quero que todas as dependências de teste estejam declaradas no `pyproject.toml`, para que qualquer membro da equipe possa instalar o ambiente de testes de forma reprodutível com um único comando.

#### Critérios de Aceitação

1. THE Sistema_de_Testes SHALL declarar as dependências de teste em um grupo de dependências opcional `[test]` ou `[dev]` no `backend/pyproject.toml`
2. THE Sistema_de_Testes SHALL incluir `pytest`, `pytest-cov`, `pytest-asyncio`, `httpx` e `hypothesis` como dependências de teste
3. THE Sistema_de_Testes SHALL especificar versões mínimas compatíveis para cada dependência de teste
4. WHEN o comando `uv sync` é executado no diretório `backend/`, THE Sistema_de_Testes SHALL instalar todas as dependências de teste necessárias
5. THE Sistema_de_Testes SHALL manter compatibilidade com Python 3.10+

### Requisito 6: Pipeline de CI com GitHub Actions

**User Story:** Como desenvolvedor, eu quero que os testes sejam executados automaticamente em pull requests para a branch `develop`, para que erros sejam detectados antes do merge e a qualidade do código seja mantida.

#### Critérios de Aceitação

1. THE Pipeline_CI SHALL ser definida em um arquivo `.github/workflows/backend-tests.yml`
2. THE Pipeline_CI SHALL ser acionada em pull requests direcionados à branch `develop`
3. THE Pipeline_CI SHALL ser acionada em pushes para branches com prefixo `feature/`
4. THE Pipeline_CI SHALL executar os testes usando Python 3.12 e o gerenciador de pacotes UV
5. THE Pipeline_CI SHALL executar os testes unitários e os testes de propriedade separadamente em jobs distintos
6. THE Pipeline_CI SHALL gerar e publicar o relatório de cobertura de código como artefato do workflow
7. IF a execução dos testes falhar, THEN THE Pipeline_CI SHALL reportar o status de falha no pull request
8. THE Pipeline_CI SHALL configurar a variável de ambiente `GOOGLE_API_KEY` com um valor de teste para que os testes de configuração funcionem corretamente

### Requisito 7: Configuração do Hypothesis para Testes de Propriedade

**User Story:** Como desenvolvedor, eu quero ter uma configuração padronizada do Hypothesis, para que os testes de propriedade sejam executados com parâmetros consistentes entre todos os desenvolvedores e no CI.

#### Critérios de Aceitação

1. THE Sistema_de_Testes SHALL configurar um perfil padrão do Hypothesis com `max_examples=200` para execução local
2. THE Sistema_de_Testes SHALL configurar um perfil `ci` do Hypothesis com `max_examples=500` para execução no pipeline de CI
3. THE Sistema_de_Testes SHALL configurar um perfil `dev` do Hypothesis com `max_examples=10` para feedback rápido durante desenvolvimento
4. THE Sistema_de_Testes SHALL registrar os perfis do Hypothesis no `conftest.py` raiz dos testes
5. WHEN a variável de ambiente `CI` está definida, THE Sistema_de_Testes SHALL ativar automaticamente o perfil `ci` do Hypothesis
6. THE Sistema_de_Testes SHALL adicionar o diretório `.hypothesis/` ao `.gitignore` do backend
