# Checklist da versão vulnerável

Esta checklist prepara a aplicação vulnerável para a marcação futura de
`v1.0-vulnerable`. Ela não autoriza publicação na Internet nem inicia a etapa de
remediação.

## Verificação automatizada

Execute na raiz do repositório:

```bash
./scripts/release-check.sh
```

O script usa, por padrão, o projeto Compose isolado `vaulta-release-check`, publica
somente em `127.0.0.1:18001` e `127.0.0.1:55432`, e remove ao terminar apenas os
containers e volumes temporários desse projeto. As portas podem ser alteradas pelas
variáveis `VAULTA_RELEASE_WEB_PORT` e `VAULTA_RELEASE_DB_PORT`.

O processo valida:

- configuração do Docker Compose e build com dependências fixadas;
- lint do código ativo, sem reformatar migrations históricas;
- checks do Django e ausência de migrations pendentes;
- suíte completa usando um banco PostgreSQL temporário;
- migrations, seed fictício e health check em uma instalação limpa.

## Gates manuais antes da tag

- confirmar que os serviços continuam ligados apenas a loopback;
- confirmar que nenhum segredo ou dado real foi incluído;
- confirmar que a interface não nomeia vulnerabilidades nem oferece pistas;
- confirmar que `evidence/` e `report/` continuam sem findings antecipados;
- revisar a matriz interna de AUTH-01 a AUTH-15 e seus testes de caracterização;
- executar um smoke test dos perfis usuário, administrador da organização e
  administrador do sistema;
- confirmar que a árvore Git está limpa e que o commit aprovado é o esperado.

Somente depois desses gates a versão deve ser integrada à linha principal e marcada
como `v1.0-vulnerable`. Correções `fix/AUTH-*` pertencem à etapa posterior ao pentest.
