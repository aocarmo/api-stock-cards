@AGENTS.md

`.claude/rules/`, `.claude/commands/`, `.claude/agents/` e `.claude/skills/` são **gerados** por
`node scripts/sync-harness.js` a partir de `docs/harness/`. Não edite lá — edite `docs/harness/`
e rode o sync.

`.claude/settings.local.json` não é gerado: é preferência local da máquina e fica fora do git.
