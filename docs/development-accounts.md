# Contas de desenvolvimento

Estas identidades são inteiramente fictícias e existem apenas na instalação local.

Execute:

```bash
docker compose exec web python manage.py seed_dev
```

| Perfil | E-mail | Senha | Finalidade |
|---|---|---|---|
| demonstração regular | `demo@vaulta.local` | `vaulta-demo` | navegação inicial e testes manuais |

O comando é idempotente e restaura a senha documentada sempre que executado. Isso é um comportamento intencional do cenário AUTH-15 e jamais deve ser adaptado para bootstrap de produção.

Outras contas fictícias serão acrescentadas com organizações, MFA e administração. Nunca substitua os valores por dados ou credenciais reais.
