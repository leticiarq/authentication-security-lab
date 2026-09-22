# Instalação e operação local

## Docker (recomendado)

1. Copie as variáveis locais: `cp .env.example .env`.
2. Inicie: `docker compose up --build`.
3. Acesse `http://127.0.0.1:8000`.
4. Verifique o processo em `http://127.0.0.1:8000/health/`.
5. Encerre com `docker compose down`.

Para criar o conjunto fictício do laboratório, execute
`docker compose exec web python manage.py seed_dev`. Ele inclui contas, organizações,
saldos, transações, acessos e notificações. As credenciais locais ficam em
`docs/development-accounts.md`.

O container web executa migrations antes do servidor de desenvolvimento. O volume `postgres_data` preserva o banco entre reinicializações. Use `docker compose down -v` somente quando quiser apagar deliberadamente todos os dados locais do laboratório.

Por padrão:

- web: `127.0.0.1:8000`;
- PostgreSQL: `127.0.0.1:5432`;
- e-mail: saída do console do container web;
- nenhum serviço externo é necessário.

Se a porta local estiver ocupada, defina `WEB_PORT` ou `POSTGRES_PORT_FORWARD` no `.env`. Não altere o bind para `0.0.0.0`.

## Python local

Requer Python 3.12 e PostgreSQL 16 disponível em loopback.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Ao executar fora do Docker, ajuste `POSTGRES_HOST=127.0.0.1` e carregue as variáveis do `.env` pelo mecanismo do seu shell. Depois:

```bash
cd app
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## Testes

Os testes rápidos usam settings isolados e banco SQLite em memória:

```bash
cd app
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test ../tests
```

Antes de preparar a versão vulnerável, execute a suíte completa em PostgreSQL e os
demais gates com:

```bash
./scripts/release-check.sh
```

O processo está detalhado em [release-checklist.md](release-checklist.md). Testes que
caracterizam uma vulnerabilidade explicam o comportamento esperado no código, sem
expor a falha na interface do produto.

## Segredos e dados

- O `.env` não é versionado.
- Os valores do `.env.example` são exclusivamente locais e deliberadamente não são segredos reais.
- Nunca insira dados pessoais, financeiros ou credenciais reais.
- `evidence/` e `report/` são espaços para uma avaliação futura; não contêm findings nesta etapa.

## Solução de problemas

- `connection refused` no banco: aguarde o health check do PostgreSQL e confira `docker compose ps`.
- porta em uso: altere apenas a porta publicada no `.env`.
- migration inconsistente: execute `python manage.py makemigrations --check --dry-run`; não edite uma migration já compartilhada sem avaliar os dados existentes.
