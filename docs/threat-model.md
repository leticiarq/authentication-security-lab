# Threat model e desenho interno dos cenários

> Documento interno da mantenedora. Não é um relatório de pentest e não afirma que qualquer finding foi observado. A matriz descreve decisões planejadas para a versão vulnerável; cada item só será considerado implementado depois de seus testes de caracterização.

## Ativos e adversário do laboratório

Ativos: credenciais fictícias, identidade de usuário, sessão autenticada, segundo fator, recuperação de conta, associação a organizações e dados financeiros simulados.

O avaliador é um usuário local sem privilégios que controla o próprio navegador, requests HTTP e scripts direcionados exclusivamente a `127.0.0.1`. Pode possuir uma conta regular própria e observar tráfego, cookies, headers, redirects, tempos e estados. Não se assume acesso inicial ao banco, container ou código durante o exercício black-box.

Fora de escopo: terceiros reais, engenharia social, indisponibilidade do host, dependências públicas, dados reais, deploy em rede e exploração de qualquer sistema que não seja esta instância local.

## Matriz interna de vulnerabilidades planejadas

| ID | Vulnerabilidade | Funcionalidade afetada | Causa planejada | Como será observável no laboratório | Complexidade |
|---|---|---|---|---|---|
| AUTH-01 | Username enumeration por resposta | login e recuperação | mensagens, status e/ou estrutura de resposta diferem quando o e-mail existe | comparação de respostas para identidades fictícias existentes e ausentes | baixa |
| AUTH-02 | Username enumeration por tempo | login | consulta antecipada retorna rápido para identidade ausente; existente executa verificação de hash custosa, sem hash fictício equivalente | amostras repetidas mostram distribuições de latência separáveis | média |
| AUTH-03 | Política fraca de senha | cadastro e alteração | formulários próprios validam apenas tamanho mínimo curto e ignoram validadores configurados no Django | senhas previsíveis são aceitas em mais de um fluxo | baixa |
| AUTH-04 | Restrição inadequada de tentativas | login | contador/lockout usa como chave um IP obtido de header de proxy não confiável e aplica janela curta apenas ao endpoint principal | proteção aparece na UI, mas tentativas distribuídas por chave controlável continuam | média |
| AUTH-05 | Armazenamento inseguro de senha | autenticação de contas legadas | `LegacyCredential` mantém digest SHA-1 rápido e sem salt para um subconjunto exclusivamente fictício; fallback de autenticação suporta a migração incompleta | inspeção autorizada do banco/código na etapa white-box evidencia digests repetíveis | média |
| AUTH-06 | Cookie de sessão inseguro | configuração de sessão | perfil vulnerável remove `HttpOnly` do cookie de sessão e mantém `Secure=False` para HTTP local | atributos do `Set-Cookie` e painel de armazenamento do navegador | baixa |
| AUTH-07 | Invalidação imprópria de sessão | alteração de senha e revogação | atualização troca a senha e preserva sessão atual, mas esquece sessões paralelas e tokens remember-me | sessão aberta em outro navegador continua funcional após a ação | baixa |
| AUTH-08 | Session fixation | conclusão do login | serviço multiestágio grava as chaves de autenticação na sessão pré-login para preservar o wizard, sem rotacionar a chave como `django.contrib.auth.login()` faria | identificador de sessão permanece idêntico antes/depois da autenticação | média |
| AUTH-09 | Recuperação de senha fraca | recuperação de conta | fluxo alternativo de suporte aceita e-mail mais informação financeira estática visível ao próprio tenant como prova suficiente | combinação de dados de baixa entropia permite avançar no fluxo local | média |
| AUTH-10 | Token de recuperação previsível | reset de senha | token numérico deriva de identificador e janela temporal por gerador pseudoaleatório não criptográfico | tokens emitidos para contas de teste apresentam padrão e espaço pequeno | média/alta |
| AUTH-11 | Falha de MFA | dispositivo confiável | cookie de dispositivo contém um identificador persistente não assinado; lookup verifica existência, mas não vincula o registro ao usuário pendente | alteração/reuso do cookie muda a exigência do segundo fator | alta |
| AUTH-12 | Bypass de fluxo de autenticação | aceite de convite multi-stage | etapa final confia em `preauth_user_id` salvo quando o convite é aberto e não exige marcador de primeiro fator concluído | navegação direta e mudanças de estado permitem concluir uma transição incompleta | alta |
| AUTH-13 | Problema em remember-me | login persistente | token determinístico, não rotacionado e não revogado por troca de senha; valor fica diretamente associado ao usuário | cookie pode ser correlacionado e permanece válido após eventos de segurança | média |
| AUTH-14 | Exposição de credencial | telemetria de suporte local | middleware diagnóstico serializa payload de POST de autenticação sem redigir campos sensíveis em arquivo local incluído em bundle de suporte acessível a system admin | credenciais fictícias aparecem em logs/bundle dentro da instalação | média |
| AUTH-15 | Credenciais padrão/demo | bootstrap de desenvolvimento | seed cria workspace de demonstração com senha documentada e conta habilitada com acesso regular | credencial publicada na documentação de desenvolvimento autentica sem troca obrigatória | baixa |

AUTH-05 terá comentários de código explícitos e próximos ao modelo/backend afirmando que o mecanismo é inseguro, limitado a dados de laboratório e proibido em produção. Esses comentários não serão enviados ao HTML.

## Conflitos e separação dos cenários

### AUTH-01 × AUTH-02

Uma resposta semanticamente diferente pode tornar o timing desnecessário. Os dois permanecem mensuráveis separadamente: AUTH-01 será caracterizado por status/corpo em recuperação e AUTH-02 pelo endpoint de login com corpo estável, porém caminho computacional diferente. O teste de timing usará várias amostras e limites tolerantes ao ambiente.

### AUTH-03 × AUTH-05

Política de criação não é o mesmo que armazenamento. Usuários normais continuam no hasher padrão do Django mesmo aceitando senhas fracas; somente contas legadas fictícias usam `LegacyCredential`. Assim, corrigir a política não corrige hashes existentes e vice-versa.

### AUTH-04 × AUTH-01/AUTH-02

O lockout não deve impedir a coleta mínima dos sinais de enumeração. A seed fornecerá várias identidades e os testes resetarão apenas dados locais. A fragilidade do rate limit estará na confiança do identificador de origem, não na ausência total de uma proteção aparente.

### AUTH-07 × AUTH-13

Sessões web e tokens persistentes serão entidades diferentes. AUTH-07 mede uma sessão Django já aberta; AUTH-13 mede a credencial remember-me capaz de criar/restaurar sessões. Cada remediação terá armazenamento e testes próprios.

### AUTH-08 × AUTH-12

Fixation trata da rotação do identificador durante um login legítimo. Bypass trata da falta de uma pré-condição em um caminho de convite. O serviço de conclusão registrará estados distintos (`password_verified`, `mfa_verified`, `invite_opened`) para que os defeitos não sejam um único `if` artificial.

### AUTH-09 × AUTH-10

AUTH-09 é fraqueza na prova de identidade do caminho alternativo; AUTH-10 é fraqueza criptográfica do token do caminho por e-mail. Serão endpoints/estratégias distintos sob a mesma experiência de recuperação.

### AUTH-11 × AUTH-12

AUTH-11 só ignora MFA depois de uma senha válida, por confiança indevida em dispositivo. AUTH-12 alcança autenticação por um fluxo de convite sem prova de primeiro fator. Os testes garantirão que um não dependa do outro.

### AUTH-14 × proibição de dados reais

Somente credenciais das contas fictícias entram na demonstração. O log ficará em volume local ignorado pelo Git, terá limite de tamanho e aviso interno. O recurso não envia nada para fora do ambiente.

## Padrões seguros do Django que serão alterados deliberadamente

| Padrão do Django | Alteração prevista | Cenário | Limite de contenção |
|---|---|---|---|
| `authenticate()` tenta um hash fictício quando usuário não existe em backends adequados | backend/serviço retorna antes dessa equivalência | AUTH-02 | somente login local customizado |
| formulários e validadores podem aplicar a política definida em `AUTH_PASSWORD_VALIDATORS` | cadastro/alteração chamam validação reduzida própria | AUTH-03 | testes caracterizam os dois fluxos afetados |
| password hashers lentos, adaptativos e com salt | fallback isolado consulta `LegacyCredential` SHA-1 sem salt | AUTH-05 | apenas usuários marcados como legados e seed fictícia |
| cookie de sessão é `HttpOnly` por padrão | override explícito no perfil vulnerável | AUTH-06 | settings de laboratório, bind em loopback |
| `login()` rotaciona/limpa a session key | conclusão multi-stage grava estado autenticado sem `cycle_key()` | AUTH-08 | serviço único, comentado e testado |
| `PasswordResetTokenGenerator` é assinado e ligado ao estado do usuário | caminho educacional usa gerador próprio previsível | AUTH-10 | sem envio externo, expiração curta não é tratada como correção |
| serializers/permissões DRF não permitem acesso anônimo por padrão neste projeto | exceções terão permission class declarada por endpoint | somente quando necessário | teste de matriz de acesso |
| `update_session_auth_hash()` rotaciona a chave da sessão atual | uso será avaliado em conjunto com o cenário de fixation | AUTH-07/AUTH-08 | testes distinguem sessão atual e sessões paralelas |

CSRF middleware, escaping de templates, ORM parametrizado e autorização por objeto não serão globalmente desativados. O laboratório é sobre autenticação; adicionar SQL injection, XSS ou quebra ampla de tenant criaria ruído e risco sem atender ao escopo.

## Critérios para aceitar cada cenário

Um cenário só entra na versão vulnerável quando:

1. nasce de uma funcionalidade normal e tem causa plausível;
2. é reprodutível com dados fictícios em uma instalação nova;
3. possui teste de caracterização que falhará após a correção;
4. não revela a resposta na interface;
5. está contido ao ambiente local;
6. pode ser corrigido sem reescrever funcionalidades não relacionadas;
7. tem nota interna apontando arquivo, serviço e decisão, sem preencher um finding de pentest.
