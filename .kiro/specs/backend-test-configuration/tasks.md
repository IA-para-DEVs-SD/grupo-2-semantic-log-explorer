# Plano de Implementação: Configuração de Testes do Backend

## Visão Geral

Implementação incremental da infraestrutura de configuração de testes do backend do Semantic Log Explorer. Cada tarefa constrói sobre a anterior, começando pela configuração central (`pyproject.toml`), passando por fixtures compartilhadas, marcadores automáticos, cobertura de código, configuração do Hypothesis, e finalizando com o pipeline de CI no GitHub Actions.

## Tarefas

- [x] 1. Criar `backend/pyproject.toml` com metadados do projeto e dependências de teste
  - Criar o arquivo `backend/pyproject.toml` com a seção `[project]` (nome: `semantic-log-explorer-backend`, versão: `0.1.0`, `requires-python = ">=3.10"`)
  - Adicionar a seção `[project.optional-dependencies]` com o grupo `test` contendo: `pytest>=8.0`, `pytest-cov>=5.0`, `pytest-asyncio>=0.24`, `httpx>=0.27`, `hypothesis>=6.100`
  - Adicionar a seção `[tool.pytest.ini_options]` com: `testpaths = ["tests"]`, `python_files = ["test_*.py"]`, `addopts = "-v"`, `asyncio_mode = "auto"`, e marcadores registrados para `unit`, `property` e `integration`
  - Adicionar as seções `[tool.coverage.run]` e `[tool.coverage.report]` com: `source = ["src"]`, `omit = ["tests/*", "*/__pycache__/*", ".venv/*"]`, `show_missing = true`, e `exclude_lines` para `if __name__`, `pass`, `...`, `pragma: no cover`
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.5_

- [x] 2. Criar `backend/tests/conftest.py` raiz com fixtures compartilhadas e perfis do Hypothesis
  - [x] 2.1 Criar o arquivo `backend/tests/conftest.py` com as fixtures `mock_settings`, `test_app`, `client` e `async_client`
    - A fixture `mock_settings` deve retornar uma instância de `Settings` com `GOOGLE_API_KEY="test-key"` e valores padrão válidos
    - A fixture `test_app` deve retornar uma instância de `FastAPI` com rotas de upload e chat incluídas e dependências mockadas (usando `dependency_overrides` para `get_settings_dep`, `get_vectorstore_service`, `get_llm_service`)
    - A fixture `client` deve retornar um `TestClient` síncrono baseado em `test_app`
    - A fixture `async_client` deve retornar um `AsyncClient` (httpx) para testes assíncronos
    - Registrar os perfis do Hypothesis: `default` (max_examples=200), `ci` (max_examples=500, suppress_health_check=[HealthCheck.too_slow]), `dev` (max_examples=10)
    - Ativar automaticamente o perfil `ci` quando a variável de ambiente `CI` estiver definida
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 2.2 Escrever teste de propriedade para a fixture `mock_settings`
    - **Propriedade 3: Fixture mock_settings retorna Settings válida**
    - Verificar que para qualquer invocação, o objeto retornado é instância de `Settings`, `GOOGLE_API_KEY` é não-vazio, `ALLOWED_EXTENSIONS` é não-vazio e `MAX_FILE_SIZE_MB` > 0
    - **Valida: Requisito 2.2**

  - [ ]* 2.3 Escrever teste de propriedade para os perfis do Hypothesis
    - **Propriedade 5: Perfis do Hypothesis com max_examples correto**
    - Verificar que para cada perfil no mapeamento `{default: 200, ci: 500, dev: 10}`, o `max_examples` corresponde ao valor esperado
    - **Valida: Requisitos 7.1, 7.2, 7.3**

- [x] 3. Criar `conftest.py` por diretório para marcadores automáticos
  - [x] 3.1 Criar `backend/tests/unit/conftest.py` com hook `pytest_collection_modifyitems` que aplica automaticamente `@pytest.mark.unit` a todos os testes coletados neste diretório
    - _Requisitos: 4.1, 4.3, 4.6_

  - [x] 3.2 Criar `backend/tests/property/conftest.py` com hook `pytest_collection_modifyitems` que aplica automaticamente `@pytest.mark.property` a todos os testes coletados neste diretório
    - _Requisitos: 4.2, 4.4, 4.6_

  - [ ]* 3.3 Escrever teste de propriedade para marcador unit
    - **Propriedade 1: Marcador unit aplicado automaticamente a testes unitários**
    - Verificar que para qualquer teste coletado de `tests/unit/`, o marcador `unit` está presente
    - **Valida: Requisitos 4.1, 4.3**

  - [ ]* 3.4 Escrever teste de propriedade para marcador property
    - **Propriedade 2: Marcador property aplicado automaticamente a testes de propriedade**
    - Verificar que para qualquer teste coletado de `tests/property/`, o marcador `property` está presente
    - **Valida: Requisitos 4.2, 4.4**

- [x] 4. Checkpoint — Verificar configuração base
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

- [x] 5. Atualizar `.gitignore` e configurar cobertura
  - Adicionar `htmlcov/` ao `.gitignore` raiz do projeto (ou criar `backend/.gitignore` se preferível) para excluir relatórios HTML de cobertura
  - Verificar que `.hypothesis/` já está no `.gitignore` (já existe no `.gitignore` raiz)
  - _Requisitos: 3.6, 7.6_

- [x] 6. Criar pipeline de CI com GitHub Actions
  - [x] 6.1 Criar o arquivo `.github/workflows/backend-tests.yml` com dois jobs paralelos: `unit-tests` e `property-tests`
    - Configurar triggers: `pull_request` para branch `develop` e `push` para branches `feature/*`
    - Ambos os jobs devem usar Python 3.12 e UV como gerenciador de pacotes
    - Ambos os jobs devem definir `GOOGLE_API_KEY=test-key-for-ci` como variável de ambiente
    - Job `unit-tests`: executar `pytest -m unit --cov --cov-report=term-missing --cov-report=html`
    - Job `property-tests`: executar `pytest -m property` (perfil `ci` ativado automaticamente via `CI=true`)
    - Job `unit-tests` deve publicar o relatório HTML de cobertura como artefato do workflow via `actions/upload-artifact`
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [ ]* 6.2 Escrever teste de propriedade para dependências de teste
    - **Propriedade 4: Dependências de teste completas e versionadas**
    - Verificar que para cada pacote em `{pytest, pytest-cov, pytest-asyncio, httpx, hypothesis}`, o pacote está presente no grupo de dependências de teste do `pyproject.toml` com especificador de versão mínima `>=`
    - **Valida: Requisitos 5.2, 5.3**

- [x] 7. Integração final e validação
  - [x] 7.1 Atualizar testes existentes em `tests/unit/test_routes.py` para utilizar as fixtures compartilhadas do `conftest.py` raiz
    - Remover as fixtures duplicadas locais (`mock_settings`, `app`, `client`, `async_client`) de `test_routes.py` que agora são fornecidas pelo `conftest.py` raiz
    - Ajustar referências se necessário para garantir compatibilidade
    - _Requisitos: 2.6, 2.7_

  - [x] 7.2 Verificar que o comando `pytest` sem argumentos descobre e executa todos os testes em `tests/unit/` e `tests/property/`
    - Executar `pytest` no diretório `backend/` e confirmar que todos os testes são coletados
    - Executar `pytest -m unit` e confirmar que apenas testes unitários são executados
    - Executar `pytest -m property` e confirmar que apenas testes de propriedade são executados
    - Executar `pytest -m "not property"` e confirmar que testes de propriedade são excluídos
    - _Requisitos: 1.6, 4.3, 4.4, 4.5_

- [x] 8. Checkpoint final — Garantir que tudo funciona
  - Garantir que todos os testes passam, perguntar ao usuário se houver dúvidas.

## Notas

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- Testes de propriedade validam propriedades universais de corretude
- Testes unitários validam exemplos específicos e casos de borda
