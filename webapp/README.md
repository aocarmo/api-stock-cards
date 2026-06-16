# Gestor de Estoque MypCards (webapp local)

Interface web local e interna (sem autenticação) para um usuário comum **cadastrar,
alterar e excluir** cartas e **acompanhar o progresso**, sobre a API existente
(`api-stock-cards`). A app embute a receita anti-429 (lotes pequenos, 1 por vez,
espera entre lotes, retry só das falhas) — o usuário não precisa saber disso.

> Não altera o backend. É só orquestração + UI sobre a API remota.

## Pré-requisitos

- Python 3.9+
- **Credenciais AWS** disponíveis pela cadeia padrão (variáveis `AWS_ACCESS_KEY_ID` /
  `AWS_SECRET_ACCESS_KEY` exportadas, ou `~/.aws/credentials`). São usadas **só para ler**
  o status do processamento na tabela DynamoDB `myp-cards-files-dev` (consulta por `s3_key`,
  pois o `file_id` do upload não bate com o do registro). Nenhum segredo é guardado no repo.

## Rodar

```bash
cd webapp
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # ajuste se necessário (sem segredos)
# garanta credenciais AWS no ambiente, ex.:
#   export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=us-east-1
python run.py                   # http://127.0.0.1:8001
```

Abra http://127.0.0.1:8001. O `●` no topo fica verde se a API remota responde (`/health`).

## Rodar em container (Colima)

A app já roda containerizada no Colima. Build a partir da **raiz do repo** (a imagem
inclui `enums/`). Porta do host **8088 → 8001** no container (8001 do host estava ocupada
por outro projeto).

```bash
colima start                       # se ainda não estiver rodando
cd webapp
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_DEFAULT_REGION=us-east-1
docker compose up -d --build       # UI: http://localhost:8088
```

As credenciais AWS são passadas pelo ambiente (não ficam na imagem nem no repo). O SQLite
dos jobs persiste em `webapp/data/` (volume). `restart: unless-stopped` mantém a app de pé
após reiniciar o Colima/máquina.

Operação:
```bash
docker compose ps            # status
docker compose logs -f       # logs
docker compose restart       # reiniciar
docker compose down          # parar e remover
```

## Telas

- **Cadastrar / Alterar** (operação `update`: preço substitui, quantidade soma): formulário
  carta-a-carta + importação em massa (colar do Excel ou CSV). 1 carta → envio imediato
  (endpoint síncrono); 2+ → job em lote.
- **Excluir**: idem, sem preço/quantidade.
- **Inventário**: busca o estoque (filtros), clicar numa carta abre Alterar pré-preenchido,
  botão Sincronizar (dispara o scrape) e Exportar CSV.
- **Progresso**: jobs em lote com barra, contagem ok/erro, lista de falhas, retry e cancelar.
  Atualiza a cada 3s.

## Configuração (`.env`)

`MYP_BASE_URL`, `DYNAMO_TABLE`, `AWS_REGION`, `BATCH_SIZE` (≤50), `BATCH_INTERVAL_SECONDS`,
`POLL_INTERVAL_SECONDS`, `POLL_TIMEOUT_SECONDS`, `MAX_RETRY_ROUNDS`, `HOST`, `PORT`, `DB_PATH`.

## Como funciona um job em massa

1. Valida e normaliza as cartas (reusa `enums/tipos_carta.py`).
2. Divide em lotes de `BATCH_SIZE` (~25).
3. Para cada lote: gera CSV em memória → `POST /upload-csv` (ou `/upload-csv-excluir`) →
   poll do DynamoDB por `s3_key` até `COMPLETED` → espera `BATCH_INTERVAL_SECONDS` (anti-429).
4. Coleta `linhas_erro`, marca cada linha ok/erro.
5. Se sobraram falhas e a rodada reduziu o total, faz **retry só das falhas** (até
   `MAX_RETRY_ROUNDS`). Falhas que não reduzem entre rodadas são tratadas como reais.

Estado persistido em SQLite (`data/jobs.db`); jobs sobrevivem a reinício do servidor.
Roda **1 job em massa por vez** para não disparar 429.
