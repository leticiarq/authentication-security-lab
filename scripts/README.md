# Scripts

Os scripts deste diretório automatizam tarefas locais, idempotentes e limitadas ao
laboratório. Eles não devem operar contra hosts públicos.

- `release-check.sh`: valida lint, migrations, testes em PostgreSQL, seed e health
  check usando um projeto Docker Compose temporário.

Nenhum script de exploração faz parte desta versão.
