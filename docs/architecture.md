# Arquitetura da aplicação

## Escopo e princípios

Vaulta é um monólito modular Django, renderizado no servidor e apoiado por PostgreSQL. Essa escolha mantém cookies, sessões, redirects e estados intermediários visíveis em um único sistema — exatamente os elementos que serão avaliados no laboratório — sem criar complexidade artificial de microsserviços.

Princípios:

1. uma aplicação única e coerente;
2. separação por domínio, não por vulnerabilidade;
3. regras de negócio em serviços, views finas e templates reutilizáveis;
4. dados exclusivamente fictícios;
5. execução local por padrão e nenhuma configuração de deploy público;
6. comportamentos inseguros catalogados e cobertos por testes de caracterização;
7. nenhuma indicação de vulnerabilidade em HTML, texto de produto ou nomes de rotas.

## Componentes planejados

| Módulo Django | Responsabilidade |
|---|---|
| `core` | páginas públicas, layout, health check e componentes comuns |
| `accounts` | usuário, perfil, cadastro, verificação de e-mail e preferências |
| `authentication` | login multiestágio, MFA, recuperação, remember-me e lockout |
| `organizations` | organizações, associação de membros, roles e convites |
| `sessions` | sessões visíveis, dispositivos confiáveis e histórico de login |
| `finance` | dashboard, contas, transações e indicadores fictícios |
| `notifications` | central de notificações locais |
| `audit` | eventos de autenticação e ações administrativas |

O Django Admin será reservado ao bootstrap e manutenção local. A área de administração do produto terá views próprias e autorização explícita por papel.

## Limites de confiança

- **Navegador → aplicação:** todos os cookies, cabeçalhos, campos ocultos e identificadores são não confiáveis.
- **Aplicação → PostgreSQL:** fonte persistente de identidade, sessão, organização e dados simulados.
- **Aplicação → e-mail local:** backend de console/arquivo; não existe provedor externo.
- **System admin → área interna:** poder global, separado do admin de organização.
- **Organização A → organização B:** isolamento por `organization_id` em toda consulta de domínio.

## Modelo de dados planejado

Campos operacionais como `created_at`, `updated_at` e UUIDs são omitidos da tabela quando repetitivos.

| Entidade | Campos principais | Relações e invariantes |
|---|---|---|
| `User` | `email`, `full_name`, `password`, `role`, `email_verified`, `is_active` | identidade global; e-mail canônico único; modelo customizado criado na primeira migration |
| `UserPreference` | `locale`, `timezone`, `currency`, `notification_flags` | 1:1 com `User` |
| `Organization` | `name`, `slug`, `status`, `plan` | contém membros e dados financeiros |
| `Membership` | `user`, `organization`, `role`, `status`, `joined_at` | única por usuário/organização; papel `member` ou `admin` |
| `Invitation` | `organization`, `email`, `role`, `token`, `expires_at`, `accepted_at`, `invited_by` | convite pertence a uma organização e tem ciclo de vida explícito |
| `FinancialAccount` | `organization`, `name`, `type`, `balance`, `currency` | apenas dados simulados; isolada por organização |
| `Transaction` | `account`, `description`, `amount`, `direction`, `occurred_on`, `category` | ledger fictício usado pelo dashboard |
| `Notification` | `user`, `kind`, `title`, `body`, `read_at` | pertencente ao usuário |
| `LoginAttempt` | `email_entered`, `user?`, `source_ip`, `user_agent`, `successful`, `reason`, `occurred_at` | registra inclusive identidade inexistente sem revelar isso na UI administrativa comum |
| `LoginSession` | `user`, `django_session_key`, `created_ip`, `last_seen_at`, `revoked_at` | espelho gerenciável da sessão Django |
| `Device` | `user`, `name`, `fingerprint`, `last_seen_at`, `trusted_until`, `revoked_at` | confiança é por usuário e tem expiração |
| `MFAProfile` | `user`, `secret`, `enabled_at` | 0..1 por usuário; segredo apenas fictício neste laboratório |
| `RecoveryCode` | `mfa_profile`, `code_digest`, `used_at` | vários por perfil MFA |
| `PasswordResetRequest` | `user`, `token`, `expires_at`, `used_at`, `requested_ip` | ciclo de recuperação auditável |
| `RememberMeToken` | `user`, `selector`, `token_material`, `expires_at`, `revoked_at` | credencial persistente separada da sessão web |
| `LegacyCredential` | `user`, `legacy_digest`, `migrated_at` | cenário controlado de compatibilidade; nunca armazena dados reais |
| `AuditEvent` | `actor?`, `organization?`, `event_type`, `metadata`, `source_ip` | trilha de ações relevantes sem ser a fonte de autorização |

`User.role` representa apenas privilégios globais (`regular` ou `system_admin`). O papel de administrador de organização pertence a `Membership.role`, evitando que um usuário vire administrador em todas as organizações.

## Endpoints planejados

As URLs públicas usam nomes de produto e não denunciam cenários de laboratório.

### Público e autenticação

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/` | landing page |
| GET | `/sobre/`, `/ajuda/`, `/termos/` | conteúdo institucional |
| GET/POST | `/cadastro/` | criação da conta |
| GET | `/verificar-email/<uidb64>/<token>/` | verificação local de e-mail |
| GET/POST | `/entrar/` | primeiro fator e opção remember-me |
| GET/POST | `/entrar/verificacao/` | desafio MFA |
| POST | `/sair/` | logout |
| GET/POST | `/recuperar-acesso/` | início da recuperação |
| GET/POST | `/redefinir-senha/<uidb64>/<token>/` | conclusão da recuperação |
| GET/POST | `/convites/<token>/` | aceite de convite |

### Área autenticada

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/app/` | dashboard financeiro |
| GET/POST | `/app/perfil/` | nome e e-mail |
| GET/POST | `/app/perfil/senha/` | alteração de senha |
| GET/POST | `/app/seguranca/` | resumo e configuração MFA |
| POST | `/app/seguranca/mfa/confirmar/` | ativação TOTP |
| POST | `/app/seguranca/mfa/desativar/` | desativação TOTP |
| POST | `/app/seguranca/codigos/renovar/` | novos recovery codes |
| GET | `/app/seguranca/acessos/` | histórico de login |
| GET | `/app/seguranca/sessoes/` | sessões e dispositivos |
| POST | `/app/seguranca/sessoes/<id>/revogar/` | revogação individual |
| POST | `/app/seguranca/sessoes/revogar-outras/` | revogação em lote |
| GET/POST | `/app/preferencias/` | preferências da conta |
| GET | `/app/notificacoes/` | notificações |

### Organização e administração

| Método | Endpoint | Papel mínimo |
|---|---|---|
| GET | `/app/organizacao/` | membro |
| GET | `/app/organizacao/membros/` | membro |
| POST | `/app/organizacao/convites/` | admin da organização |
| POST | `/app/organizacao/membros/<id>/papel/` | admin da organização |
| POST | `/app/organizacao/membros/<id>/remover/` | admin da organização |
| GET | `/controle/` | system admin |
| GET | `/controle/usuarios/` | system admin |
| GET | `/controle/organizacoes/` | system admin |
| POST | `/controle/usuarios/<id>/status/` | system admin |
| GET | `/api/v1/dashboard/summary/` | usuário autenticado; resposta JSON para widgets |

Endpoints que mudam estado usarão POST e CSRF, exceto onde o comportamento vulnerável planejado exigir uma decisão específica e documentada.

## Fluxos de autenticação

### Cadastro e verificação

1. visitante envia nome, e-mail e senha;
2. serviço cria usuário inativo no sentido de e-mail não verificado, mas capaz de iniciar sessão limitada;
3. token de verificação é enviado ao backend de e-mail local;
4. link marca `email_verified` e libera funções sensíveis;
5. aceite de convite associa a conta à organização correspondente.

### Login, MFA e remember-me

1. e-mail e senha são processados e um `LoginAttempt` é criado;
2. conta sem MFA conclui a autenticação;
3. conta com MFA entra em estado `pending_mfa` vinculado à tentativa;
4. TOTP, recovery code ou dispositivo confiável conclui o segundo estágio;
5. uma sessão e um dispositivo aparecem na área de segurança;
6. se solicitado, remember-me restaura uma sessão futura por cookie persistente.

### Recuperação de senha

1. visitante solicita recuperação da conta;
2. uma `PasswordResetRequest` é persistida e o e-mail local recebe o link;
3. o token abre o formulário de nova senha;
4. conclusão atualiza a credencial, registra evento e conduz ao login.

### Alteração de senha e sessões

1. usuário autenticado confirma a senha atual;
2. nova senha é gravada;
3. sessão atual é preservada para continuidade;
4. sessões, remember-me e dispositivos que deveriam ser revogados seguem a política implementada na versão em questão;
5. usuário pode revisar e revogar sessões pela interface.

### Convite de organização

1. administrador cria convite para e-mail e papel definidos;
2. backend local entrega link com token;
3. usuário existente confirma o vínculo ou novo usuário passa pelo cadastro;
4. aceite atômico cria `Membership` e consome o convite.

## Autorização

Views recebem decorators/mixins por capacidade: `login_required`, `organization_member_required`, `organization_admin_required` e `system_admin_required`. Templates podem esconder ações, mas nunca serão a fonte da autorização. Serviços sempre recebem o ator e a organização efetiva; IDs enviados pelo navegador não definem sozinhos o tenant.

## Decisões de implementação

- Django Templates favorecem inspeção transparente de requests e redirects e dispensam toolchain frontend.
- DRF será usado apenas nos widgets que realmente pedem JSON; não haverá uma API paralela sem necessidade.
- PostgreSQL é a fonte de verdade em desenvolvimento; SQLite fica restrito aos testes unitários rápidos.
- UUIDs evitam expor contagens triviais, mas não substituem autorização.
- Serviços de autenticação terão interfaces pequenas para permitir trocar o comportamento vulnerável por sua remediação sem reescrever as views.
