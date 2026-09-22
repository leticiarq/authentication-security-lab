# Manual do laboratório — Vaulta

## Apresentação

Vaulta é uma plataforma SaaS fictícia de gestão financeira para pequenas empresas.
Ela reúne contas, lançamentos, notificações, equipes e configurações de segurança em
uma aplicação Django única. Todos os nomes, saldos, acessos e organizações são
inventados.

Este ambiente foi criado para uma avaliação de segurança de autenticação em contexto
realista. A interface se comporta como um produto comum e não identifica os cenários
que devem ser encontrados. O objetivo do participante é observar o sistema, formular
hipóteses, validá-las somente no ambiente local e registrar evidências próprias.

> **Atenção:** a aplicação é intencionalmente vulnerável. Execute-a apenas em uma
> máquina local ou rede isolada. Nunca publique seus serviços na Internet.

## O que existe no produto

- páginas públicas, cadastro e verificação local de e-mail;
- login, opção de permanência, logout e recuperação de acesso;
- configurações de senha, MFA/TOTP e códigos de recuperação;
- histórico de acessos, sessões e dispositivos reconhecidos;
- dashboard com saldos e lançamentos financeiros fictícios;
- organizações com membros, administradores e convites;
- administração global de usuários e organizações.

Os perfis de negócio são:

- **usuário regular:** utiliza o workspace ao qual pertence;
- **administrador da organização:** também gerencia membros e convites do próprio
  workspace;
- **administrador do sistema:** utiliza a área interna da plataforma.

## Preparação

Na raiz do repositório:

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py seed_dev
```

A aplicação fica disponível em `http://127.0.0.1:8000`. Se essa porta estiver
ocupada, adicione `WEB_PORT=18000` ao `.env` e use
`http://127.0.0.1:18000`.

Para uma primeira navegação autenticada, use a conta de demonstração fornecida ao
operador em [development-accounts.md](development-accounts.md). O seed cria outros
usuários, organizações, saldos, lançamentos, dispositivos, acessos e convites para
que a aplicação não dependa de cadastro manual.

E-mails de verificação e recuperação são simulados. Consulte-os com:

```bash
docker compose logs -f web
```

## Artefatos fornecidos

O diretório [`lab-data/`](../lab-data/) representa materiais que poderiam ter sido
obtidos antes da avaliação. Ele contém uma pequena amostra sintética de credenciais
expostas. Os registros podem estar corretos, incorretos ou desatualizados; o arquivo
não informa quais identidades existem atualmente e não substitui a validação do
participante.

Nenhum item desse diretório contém dados reais. Os domínios terminam em `.local` e
seu uso é autorizado exclusivamente contra esta instância local da Vaulta.

## Escopo da avaliação

Está dentro do escopo:

- a aplicação Vaulta iniciada por este repositório;
- os serviços publicados pelo Compose somente em `127.0.0.1`;
- as contas e os dados gerados por `seed_dev`;
- requisições feitas pelo navegador, DevTools, proxy local ou scripts próprios;
- os artefatos sintéticos em `lab-data/`.

Está fora do escopo:

- qualquer host, conta, domínio ou serviço externo;
- indisponibilizar a máquina ou consumir recursos sem limite;
- inserir credenciais, dados pessoais ou informações financeiras reais;
- alterar a implementação antes de concluir a coleta de evidências.

## Roteiro de trabalho sugerido

1. navegue pelos fluxos públicos e autenticados como um usuário comum;
2. registre endpoints, transições de estado, redirects, cookies e respostas;
3. compare comportamentos entre identidades, perfis e sessões diferentes;
4. revise os fluxos de recuperação, permanência, MFA e gerenciamento de sessão;
5. valide cada hipótese de forma controlada e reproduzível;
6. guarde somente suas próprias evidências em `evidence/`;
7. redija findings em `report/` apenas depois da avaliação.

O manual deliberadamente não apresenta uma lista de vulnerabilidades, payloads,
respostas esperadas ou critérios que confirmem um finding. Para preservar o exercício,
o participante não deve consultar `docs/threat-model.md`, testes de caracterização ou
comentários internos do código antes de terminar a análise.

## Reinicialização do ambiente

O seed é idempotente e pode restaurar o conjunto básico sem duplicar registros:

```bash
docker compose exec web python manage.py seed_dev
```

Para apagar todo o banco local e reconstruir do zero, encerre o ambiente e remova o
volume deliberadamente:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec web python manage.py seed_dev
```

O comando com `-v` elimina permanentemente os dados locais do laboratório.

## Encerramento

```bash
docker compose down
```

Isso encerra os containers sem apagar o volume PostgreSQL.
