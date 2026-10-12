# Como trabalhar neste repo

## O que este repo é

Ferramenta de apoio pessoal. O dono roda isso para gerenciar o próprio estoque de cartas.
O critério de qualidade é **funciona e é fácil de entender daqui a seis meses** — não é
cobertura de teste, não é arquitetura, não é padrão de mercado.

## Regras

1. **Não refatore por iniciativa própria.** Se a tarefa é "arruma o filtro do inventário",
   arrume o filtro do inventário. Não extraia camada, não crie interface, não renomeie em
   massa, não introduza injeção de dependência.

2. **Não introduza testes, linters ou CI sem pedirem.** Não há testes hoje e isso é uma
   escolha. Adicionar `pytest` porque "é boa prática" é aumentar o custo de manutenção de uma
   ferramenta de uma pessoa só.

3. **Mudança cirúrgica.** Menor diff possível. Prefira editar o arquivo que já existe a criar
   um novo.

4. **Escreva em português.** Código, comentários, docs, mensagens de commit. É a língua do
   repo inteiro.

5. **Encontrou algo torto que não faz parte da tarefa?** Fale, não conserte. Boa parte já está
   catalogada em `projeto.md` na seção "Estado real".

6. **Lógica nova vai para a API Lambda**, como endpoint em `routes/` + caso de uso em
   `use_cases/`. Não crie script solto na raiz para "rodar à mão" — foi exatamente isso que
   gerou os oito arquivos mortos que já removemos.

7. **Antes de mover ou renomear arquivo Python**, procure a linha de `import` de quem usa ele —
   não o nome solto. Nomes se repetem entre rota, método de service e arquivo.

## Verificação antes de dizer que terminou

Não há suíte de testes para rodar. O que dá para fazer:

```bash
# tudo compila?
python3 -m compileall -q main.py routes use_cases services dtos enums lambdas

# a webapp importa sem erro? (o venv dela é webapp/.venv)
cd webapp && .venv/bin/python -c "import config; from app.main import app; print('ok')"

# o template SAM é válido?
sam validate --lint
```

Só a `webapp/` tem venv (`webapp/.venv`). A API da raiz não tem — o deploy instala as
dependências no build do SAM. Se precisar rodar a API local, crie um venv na hora com
`requirements.txt`.

Se mexeu na webapp, suba ela (`cd webapp && .venv/bin/python run.py`) e abra a tela que mudou.
É uma UI — olhe.

## O que nunca fazer

- Rodar deploy (`sam deploy`) ou dar push em `develop`/`staging`/`main` sem pedirem: as três
  branches disparam deploy automático na AWS.
- Apagar ou sobrescrever `.env`, `webapp/.env` ou `webapp/data/jobs.db`.
- Editar `.claude/rules/`, `.claude/commands/`, `.claude/agents/` ou `.claude/skills/` — são
  gerados a partir de `docs/harness/`. Ver `docs/harness/README.md`.
