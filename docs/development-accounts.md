# Contas de desenvolvimento

Estas identidades são inteiramente fictícias e existem apenas na instalação local.

Execute:

```bash
docker compose exec web python manage.py seed_dev
```

| Perfil | E-mail | Senha | Finalidade |
|---|---|---|---|
| administrador da Aurora Studio | `demo@vaulta.local` | `vaulta-demo` | navegação inicial e gestão da organização |
| membro da Aurora Studio | `analista@aurora.local` | `aurora-analista` | perfil regular e histórico fictício |
| financeiro da Aurora Studio | `financeiro@aurora.local` | `fluxo-2024` | perfil regular e dados financeiros |
| administradora da Nébula Comércio | `marina@nebula.local` | `nebula-local` | segundo tenant e gestão da organização |
| membro da Nébula Comércio | `caio@nebula.local` | `vendas-2025` | segundo tenant como usuário regular |
| administrador do sistema | `admin@vaulta.local` | `vaulta-admin` | área `/controle/` |
| conta legada | `legacy@vaulta.local` | `welcome123` | compatibilidade fictícia de autenticação |

O seed cria três organizações, incluindo um tenant suspenso para a área administrativa.
Aurora Studio e Nébula Comércio recebem membros, contas financeiras, lançamentos,
notificações e convites. Também são gerados dispositivos, sessões inventariadas e
eventos de login fictícios para preencher as telas de segurança.

O comando é idempotente e restaura as senhas documentadas sempre que executado. Esse
comportamento existe somente para tornar o laboratório reproduzível e jamais deve ser
adaptado para bootstrap de produção.

Nunca substitua os valores por dados ou credenciais reais.
