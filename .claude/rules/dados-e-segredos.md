# Dados e segredos

## Nada de dado versionado

Este repo versiona **código**. CSV de carga, inventário exportado, banco de jobs, dump de
scraping — nada disso entra no git. Já são cobertos pelo `.gitignore`.

Quando um script gerar arquivo, ele vai para `data/` (ignorada) ou para o diretório temporário.
Nunca para a raiz. A raiz já ficou com 48 CSVs soltos uma vez.

## Segredos

Credenciais existem em três lugares, e só nesses três:

| Onde                          | O quê                                        | Versionado? |
| ----------------------------- | -------------------------------------------- | ----------- |
| `.env` (raiz)                 | AWS + login do MypCards, para os scripts      | não         |
| `webapp/.env`                 | AWS (leitura do DynamoDB) + config da webapp  | não         |
| Secrets do GitHub Actions     | AWS, para o deploy SAM                        | n/a         |

`webapp/.env.example` é o template público — mantenha ele **sem valor nenhum de segredo**.

## Nunca coloque credencial em outro lugar

Em especial:

- **Não** em `.claude/settings.local.json`. Um comando como
  `Bash(export AWS_ACCESS_KEY_ID="AKIA...")` na lista de permissões grava a chave em texto
  plano e a entrega para dentro do contexto de qualquer agente que abrir o arquivo. Já
  aconteceu neste repo. Permita o padrão (`Bash(export AWS_ACCESS_KEY_ID=*)`), nunca o valor.
- **Não** em `docker-compose.yml`, `template.yaml` ou qualquer `.md`. O compose já faz o certo:
  lê do ambiente (`${AWS_ACCESS_KEY_ID:-}`).
- **Não** cole chave em prompt para o agente. Exporte no shell e mande ele usar o ambiente.

Se uma chave vazar, o conserto é **revogar no IAM**, não apagar o arquivo — ela já saiu.
