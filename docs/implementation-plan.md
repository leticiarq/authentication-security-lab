# Plano de implementação

O trabalho usa branches de capacidade. Vulnerabilidades entram junto à funcionalidade que as produz; nenhuma branch `AUTH-*` será criada antes da etapa de remediação.

## Fase 1 — Fundação (`feat/project-setup`)

Estado: implementada em `feat/project-setup`.

- arquitetura, modelo de dados, endpoints, fluxos e threat model;
- Django e settings separados;
- PostgreSQL, Docker e bind local;
- usuário customizado e migration inicial;
- layout responsivo e páginas landing, sobre, ajuda e termos;
- health check e testes básicos;
- estrutura de evidências, findings futuros e scripts.

Não há comportamento vulnerável de autenticação nesta fase.

## Fase 2 — Contas e organizações

Estado: cadastro e verificação local implementados em `feat/user-registration`; organizações, memberships contextuais, gestão de membros e convites para contas existentes implementados em `feat/organizations`.

Branches sugeridos: `feat/user-registration`, `feat/organizations`.

- cadastro e verificação local de e-mail;
- perfil, preferências e alterações de identidade;
- organizações, memberships, convites e isolamento de tenant;
- seeds idempotentes para usuários, organizações e papéis;
- introdução controlada de AUTH-03, parte de AUTH-12 e AUTH-15.

Gate: migrations reproduzíveis, matriz de acesso por papel e cadastro completo testado.

## Fase 3 — Autenticação e recuperação

Estado: autenticação primária, histórico, proteção de tentativas, remember-me e conta demo implementados em `feat/authentication-flow`; recuperação por e-mail, expiração e redefinição implementadas em `feat/password-recovery`. O caminho assistido de AUTH-09 permanece pendente.

Branches sugeridos: `feat/authentication-flow`, `feat/password-recovery`.

- login/logout, remember-me, lockout e histórico;
- recuperação e redefinição de senha;
- backend legado restrito;
- AUTH-01, AUTH-02, AUTH-04, AUTH-05, AUTH-09, AUTH-10, AUTH-13 e AUTH-14;
- testes funcionais e de caracterização.

Gate: cada fluxo funciona pelo navegador e tem estados/erros coerentes; testes distinguem comportamentos deliberados de regressões acidentais.

## Fase 4 — Sessões e MFA

Estado: inventário de sessões, dispositivos, histórico e revogação implementados em `feat/session-management`; TOTP, recovery codes, dispositivos confiáveis e transições multi-stage implementados em `feat/mfa`.

Branches sugeridos: `feat/session-management`, `feat/mfa`.

- sessões, dispositivos, revogação e histórico visível;
- TOTP, recovery codes e dispositivos confiáveis;
- AUTH-06, AUTH-07, AUTH-08 e AUTH-11;
- conclusão do cenário multi-stage AUTH-12.

Gate: testes com dois clientes independentes e relógio controlado; nenhum segredo ou QR code real versionado.

## Fase 5 — Produto financeiro e administração

Branches sugeridos: `feat/financial-dashboard`, `feat/administration`.

- contas e transações fictícias;
- dashboard e widgets JSON;
- notificações;
- administração de organização e área de system admin;
- seed completa e visual polish.

Gate: jornadas por papel, responsividade, acessibilidade básica e isolamento por organização.

## Fase 6 — Estabilização vulnerável

Branch sugerido: `chore/vulnerable-release`.

- instalação limpa via Docker;
- suíte completa, lint e revisão de migrations;
- validação de todos os 15 cenários somente em localhost;
- congelamento das contas de desenvolvimento;
- revisão para garantir que UI/HTML não entregam pistas;
- checklist de ausência de segredos e dados reais.

Quando estável, merge em `main` e tag `v1.0-vulnerable`. Isso ainda não inclui relatório nem correções.

## Etapas posteriores, fora do escopo atual

Após pentest independente: findings em `vulnerabilities/AUTH-*/`, evidências em `evidence/` e relatório em `report/`. Só então cada remediação poderá usar `fix/auth-01-...`, com comparação de comportamento e teste de regressão. A versão hardened receberá tag própria depois que todas as correções forem validadas.

## Estratégia de testes

- **unitários:** serviços, tokenização, autorização e regras de formulário;
- **integração:** views + sessão + PostgreSQL para estados transacionais;
- **jornada:** cadastro, login, MFA, recuperação, convite e revogação com clientes distintos;
- **caracterização:** preservam exatamente o comportamento vulnerável intencional;
- **não regressão comum:** CSRF, isolamento de organização, escaping e autorização que não fazem parte dos cenários.

Testes de tempo serão estatísticos e separados da suíte rápida para reduzir flakiness. Testes de cookie examinarão atributos de resposta; testes de sessão usarão dois `Client` independentes.
