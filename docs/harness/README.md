# Harness — update-myp

`docs/harness/` é a **fonte única** do contexto para agentes de IA neste repo.

O que está em `.claude/rules/`, `.claude/commands/`, `.claude/agents/` e `.claude/skills/` é
**gerado** — não edite lá, o próximo sync sobrescreve. Edite aqui e rode:

```bash
node scripts/sync-harness.js           # sincroniza
node scripts/sync-harness.js --check   # só verifica (sai 1 se estiver desatualizado)
```

Não precisa de `npm install`: é JS puro, roda em qualquer Node.

## Duas exceções, que **não** são geradas

| Arquivo                      | Por quê                                                                  |
| ---------------------------- | ------------------------------------------------------------------------ |
| `AGENTS.md` (raiz)           | Precisa estar na raiz para o `@AGENTS.md` do `CLAUDE.md` carregar sozinho |
| `.claude/settings.local.json`| Preferência local da máquina, nunca versionada                           |

## Estrutura

```
docs/harness/
├── README.md      # este arquivo
├── rules/         # regras carregadas como contexto (*.md)
├── commands/      # slash commands (*.md) — vazio hoje
├── agents/        # subagents (*.md) — vazio hoje
└── skills/        # skills (uma pasta por skill) — vazio hoje
```

As pastas vazias são intencionais: marcam onde cada coisa entra se um dia fizer falta. O sync
lida com pastas vazias sem reclamar.

## Escopo

Este é um repo de **ferramenta de apoio pessoal**, não um serviço de produção com equipe. O
harness aqui é deliberadamente pequeno — três regras. Se ele começar a crescer para além do
que é verdade sobre o repo, ele passou do ponto.
