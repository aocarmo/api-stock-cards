# Projeto: update-myp

Automação de estoque de cartas no **MypCards** — cadastrar, atualizar, excluir e inventariar
cartas em massa, contornando o rate limit (429) do site.

Ferramenta de apoio pessoal do dono do repo. Não é serviço de produção, não tem equipe, não tem
SLA.

## As duas metades do repo

### 1. API serverless (raiz) — deployada na AWS

FastAPI atrás do Mangum, empacotada com **AWS SAM** e deployada por GitHub Actions.

| Caminho              | O que é                                                                |
| -------------------- | ---------------------------------------------------------------------- |
| `main.py`            | App FastAPI (só configuração + rota raiz)                              |
| `routes/routes.py`   | Todos os endpoints `/api/v1/*`                                         |
| `use_cases/`         | Regra de negócio, um arquivo por caso de uso                           |
| `services/`          | `myp_service.py` — cliente do site MypCards (cloudscraper + BeautifulSoup) |
| `dtos/`, `enums/`    | Modelos Pydantic e normalização de tipo/idioma de carta                |
| `lambdas/`           | Handlers Lambda: api, producer, consumer, csv_trigger, inventory_scraper |
| `template.yaml`      | Infra SAM: API Gateway, S3, SQS, DynamoDB, Lambdas                     |
| `samconfig.toml`     | Parâmetros de deploy do SAM                                            |

Fluxo de massa: upload CSV → S3 → Lambda producer → SQS → até 50 consumers → DynamoDB.

Deploy é automático por branch: `develop` → dev, `staging` → staging, `main` → prod
(`.github/workflows/`). Credenciais vêm de secrets do GitHub.

### 2. `webapp/` — UI local, roda na sua máquina

FastAPI + Jinja2 + SQLite, por cima da API remota acima. Sem autenticação, uso local.
Embute a receita anti-429: lotes pequenos, um por vez, espera entre lotes, retry só das falhas.

Detalhes de como rodar (host-native na 8001, container na 8088), telas e variáveis:
**`webapp/README.md`** — está correto e atualizado, siga ele.

### Nada de script local

**Toda a lógica vive na API Lambda.** A raiz não tem mais script avulso e não deve voltar a ter.

Havia oito utilitários de linha de comando (exportar inventário, excluir em massa, scraping,
precificação dinâmica) — todos removidos em agosto/2026. A API já faz o que eles faziam, e o
que precisa de UI está na `webapp/`.

Se aparecer a necessidade de "rodar uma coisinha à mão", a resposta é **um endpoint na API**,
não um `.py` na raiz. O único `.py` da raiz é `main.py`, e ele só configura o app FastAPI.

## Stack

Python 3.11 · FastAPI · Pydantic · boto3 · cloudscraper + BeautifulSoup4 · Mangum · AWS SAM
(Lambda, API Gateway, S3, SQS, DynamoDB) · GitHub Actions.

Dependências: `requirements.txt` (API) e `webapp/requirements.txt` (webapp) — são conjuntos
separados, com versões diferentes de FastAPI de propósito.

## Estado real (não conserte sem pedirem)

Coisas conhecidamente tortas. Estão documentadas para o agente não "descobrir" e sair
arrumando por conta própria:

- **Não há testes**, e não há config de teste — `pytest.ini` e `requirements-test.txt` foram
  removidos porque apontavam para uma pasta `tests/` que nunca existiu.
- **`webapp/docker-compose.yml` e `webapp/README.md` divergem** na porta interna (8010 vs 8001).
- **`PricingQueue` no `template.yaml` é infra morta** — nenhuma Lambda produz ou consome dela.
  Sobrou da precificação dinâmica, que foi removida. Remover apaga a fila na AWS no próximo
  deploy, então é decisão do dono.
- **O login automático no MypCards está morto.** Desde 04/09/2026 o site exige reCAPTCHA no
  login, então `MypService.login()` só imprime o aviso e devolve `False`. A sessão vem do
  navegador do dono via `POST /api/v1/sessao` (cookie `_identity`), gravada no DynamoDB
  (tabela de arquivos, item `sessao_myp`). `MYP_USERNAME`/`MYP_PASSWORD` no `template.yaml`
  não servem mais para nada — e são segredo em arquivo versionado; remover é decisão do dono.
  Detalhes em `docs/API_USAGE.md` §0.
- **O nick da conta mudou de `aocarmo` para `Cardoris`.** `MYP_USERNAME_URL=aocarmo` no
  `template.yaml` dá 404 no site; o nick certo vem junto com a sessão, então a variável virou
  só fallback.
- **Não há mais agendamento de scraping.** Existia um `Schedule: rate(1 day)` num bloco
  duplicado de `InventoryScraperFunction`; o bloco foi removido junto com a duplicação, por
  decisão do dono. O scraping roda sob demanda (botão Sincronizar da webapp).
