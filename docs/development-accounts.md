# Contas de desenvolvimento

Estas identidades são inteiramente fictícias e existem apenas na instalação local.

Execute:

```bash
docker compose exec web python manage.py seed_dev
```

| Perfil | E-mail | Senha | Finalidade |
|---|---|---|---|
| administrador da Aurora Studio | `demo@vaulta.local` | `vaulta-demo` | navegação inicial e gestão da organização |

O seed também cria `analista@aurora.local` como membro regular com senha inutilizável. Essa identidade serve para telas administrativas e não autentica diretamente.

O comando é idempotente e restaura a senha documentada sempre que executado. Isso é um comportamento intencional do cenário AUTH-15 e jamais deve ser adaptado para bootstrap de produção.

Outras contas fictícias serão acrescentadas com organizações, MFA e administração. Nunca substitua os valores por dados ou credenciais reais.
