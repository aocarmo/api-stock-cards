# update-myp — contexto para agentes

Automação de estoque de cartas no MypCards. **Ferramenta de apoio pessoal**, uma pessoa só,
sem SLA. O objetivo é funcionar e continuar legível — não é arquitetura nem cobertura de teste.

O repo tem duas metades: uma **API serverless** na raiz (FastAPI + AWS SAM, deployada na AWS) e
uma **UI local** em `webapp/` que consome essa API embutindo a receita anti-429.

## Leia primeiro

| Regra                                | Quando                                                    |
| ------------------------------------ | --------------------------------------------------------- |
| `docs/harness/rules/comportamento.md`| Sempre. Diz o que **não** fazer aqui (não refatorar, etc.) |
| `docs/harness/rules/projeto.md`      | Sempre. Stack, o que é cada pasta, o que já está torto     |
| `docs/harness/rules/dados-e-segredos.md` | Ao mexer em CSV, `.env`, credencial ou `.gitignore`    |

Para rodar a webapp: `webapp/README.md`. Para os endpoints da API: `docs/API_USAGE.md`.

## Resumo de uma linha por regra

- **Não refatore, não adicione testes, não introduza padrão** sem pedirem explicitamente.
- **Português** em tudo: código, comentários, commits, docs.
- **Nenhum dado no git** — CSV, `.db`, export. Nenhum segredo fora dos dois `.env`.
- **Toda lógica na API Lambda** (`routes/` + `use_cases/`). Nada de script solto na raiz para
  "rodar à mão" — os oito que existiam foram removidos.
- **Não rode `sam deploy` nem dê push em `develop`/`staging`/`main`** — as três disparam
  deploy automático na AWS.

## Harness

`docs/harness/` é a fonte única; `.claude/rules|commands|agents|skills` são **gerados**.
Editou o harness, rode:

```bash
node scripts/sync-harness.js           # sincroniza
node scripts/sync-harness.js --check   # verifica se está em dia
```

Detalhes em `docs/harness/README.md`.
