# MypCards API — Guia operacional (cadastro/atualização em massa)

Guia prático para cadastrar/atualizar/excluir cartas em massa via API. Foco em
"como fazer", com as armadilhas reais (throttling 429) já mapeadas.

> **Regra de ouro descoberta na prática:** o gargalo é o **429 do MypCards**.
> Mande arquivos **≤ 50 linhas** (1 chunk = 1 consumer) e **espaçados 2–3 min**.
> Arquivos grandes disparam até 50 consumers em paralelo, o MypCards bloqueia, e
> as falhas voltam mascaradas como `produto_nao_encontrado` (ver §5).

---

## 1. Base

```
BASE=https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1
```

AWS (para checar status no DynamoDB) — **exporte as credenciais, não as versione**:

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"
```

| Recurso | Valor |
|---|---|
| Tabela de status (DynamoDB) | `myp-cards-files-dev` |
| Bucket S3 | `myp-cards-csv-dev-215689610032` |
| Conta AWS | `215689610032` |

---

## 2. Formato do CSV

```
numero,colecao,tipo,idioma,preco,quantidade
021/182,DRI,normal,portugues,0.30,29
008/182,DRI,foil,portugues,0.99,12
002/182,DRI,reverse-foil,portugues,0.99,2
```

- **Exclusão** dispensa `preco,quantidade`: só `numero,colecao,tipo,idioma`.
- `tipo`: `normal`, `foil`, `reverse-foil`, `pokeball-foil`, `masterball-foil`,
  `full-art`, `altered-art`, `promo`, `staff` (mapeado em `services/myp_service.py`).
- `numero` no formato `NNN/182` (zero à esquerda). Vale inclusive secret rares
  (ex.: `237/182`).

---

## 3. Endpoints de upload (assíncrono, em massa)

Todos respondem `{ message, file_id, s3_key, total_linhas }` e processam em background.

### Cadastrar/atualizar — `POST /upload-csv` com `operation=update`
```bash
curl -s -X POST "$BASE/upload-csv" \
  -F "file=@arquivo.csv" \
  -F "operation=update"
```
`operation` aceita `update | delete | recadastrar`. Cada um grava num prefixo S3
diferente (`csv-uploads/`, `csv-excluir/`, `csv-recadastrar/`).

### Excluir — `POST /upload-csv-excluir`
```bash
curl -s -X POST "$BASE/upload-csv-excluir" -F "file=@excluir.csv"
```
CSV só com `numero,colecao,tipo,idioma`.

### Recadastrar (exclui e recria) — `POST /upload-csv-recadastrar`
```bash
curl -s -X POST "$BASE/upload-csv-recadastrar" -F "file=@arquivo.csv"
```

> Só **1 arquivo é processado por vez**. Se houver outro em andamento pode voltar
> **429**. Sempre espere `COMPLETED` antes do próximo (ver §4).

---

## 4. Acompanhar status

O `upload-csv` devolve `s3_key`. Pode-se buscar por `s3_key` (scan) ou por
`file_id` (mais barato, via GET).

### Por s3_key (DynamoDB scan)
```bash
KEY="csv-uploads/20260615_192321_dri_pt_foil_ready.csv"
aws dynamodb scan --table-name myp-cards-files-dev \
  --filter-expression "s3_key = :k" \
  --expression-attribute-values "{\":k\":{\"S\":\"$KEY\"}}" \
  --projection-expression "#s" --expression-attribute-names '{"#s":"status"}' \
  --query "Items[0].status.S" --output text
```

### Por file_id (endpoint)
```bash
curl -s "$BASE/status/file_20260615_192321"
```

**Status:** `PENDING` → `PROCESSING` → `COMPLETED` | `FAILED`.

### Ver as linhas que falharam
```bash
aws dynamodb scan --table-name myp-cards-files-dev \
  --filter-expression "s3_key = :k" \
  --expression-attribute-values "{\":k\":{\"S\":\"$KEY\"}}" \
  --query "Items[0].linhas_erro" --output json
```
`linhas_erro` é uma lista de `{numero, colecao, tipo, idioma, status}`.
**Sucesso real = `total_linhas − len(linhas_erro)`** (não há contador de sucesso;
a tabela só guarda `total_linhas`, `chunks_processados`, `linhas_erro`).

---

## 5. Semântica de cada operação e os status de erro

Caminho assíncrono: `producer` quebra em **chunks de 50 linhas** → SQS → vários
**consumers em paralelo** (`lambdas/consumer.py` → `use_cases/*massa*`).

### `operation=update` (`AtualizarMassaUseCase`) — **cria ou atualiza**
1. `search_card(numero, colecao, tipo, idioma)` na sua pasta → se acha,
   **atualiza** (status `atualizada`): soma a quantidade, substitui o preço.
2. Se não acha → `search_product_id(numero, colecao)` no catálogo
   (**ignora tipo/idioma**, busca por `term=numero`) → se acha, **cria**
   (`criada`); se a criação falha, `erro_criar`.
3. Se o produto não é achado no catálogo → `produto_nao_encontrado`.

| status | significado |
|---|---|
| `atualizada` / `criada` | ✅ sucesso |
| `erro_atualizar` | achou na pasta mas o update falhou |
| `produto_nao_encontrado` | `search_product_id` voltou vazio — **muitas vezes 429**, não carta inexistente (ver §6) |
| `erro_criar` | achou o produto mas a criação falhou |
| `erro` | exceção |

### `operation=recadastrar` (`RecadastrarMassaUseCase`) — exclui e recria
Sucesso: `ok` / `criada`. Erro: `erro_deletar`, `produto_nao_encontrado`,
`erro_cadastrar`, `erro`.

### `operation=delete` — exclui
Sucesso: `excluida`, `nao_encontrada`. Qualquer outro = erro.

---

## 6. A armadilha do `produto_nao_encontrado` (lição da sessão de 2026-06-15)

`search_product_id` faz `GET mypcards.com/produto/search?term=<numero>` e, se o
JSON vier vazio ou der erro (ex.: **429 por excesso de requisições**), retorna
`None` silenciosamente → vira `produto_nao_encontrado`. **Não significa, na
maioria das vezes, que a carta não existe.**

Evidência: enviar o arquivo cheio de 145 normais deu **46% de
`produto_nao_encontrado`**; reenviar exatamente as mesmas em **lotes de 25 linhas
deu 0 erro**. O produto sempre existiu — era throttling.

**Como confirmar se é throttle vs. carta inexistente:** `search_product_id` só
precisa de `numero + colecao`. Se o número existe em qualquer linha daquela
coleção num inventário conhecido, então o produto existe e o erro foi falso
negativo (reenviar menor resolve).

---

## 7. Receita recomendada (cadastro em massa sem 429)

1. Garanta que nenhum arquivo está em `PROCESSING`.
2. Quebre o CSV em arquivos de **≤ 50 linhas** (idealmente ~25 → 1 consumer só).
3. Envie **1 por vez** com `operation=update`, esperando `COMPLETED` + **2–3 min**
   entre eles.
4. Ao final, leia `linhas_erro` de cada um, junte os `numero` que falharam,
   **monte um CSV só com as falhas** e repita (loop) até `linhas_erro` zerar.
   Reenviar só as falhas é seguro: como não foram criadas, não há duplo-incremento
   de quantidade.

Quebrar em lotes de 25 (preservando o header):
```bash
HDR="numero,colecao,tipo,idioma,preco,quantidade"
tail -n +2 origem.csv > _rows.txt
split -l 25 _rows.txt _part_
i=1; for f in _part_*; do { echo "$HDR"; cat "$f"; } > "batch_$(printf '%02d' $i).csv"; i=$((i+1)); done
rm -f _part_ _rows.txt
```

> Há um script de exemplo desta sessão em
> `dri-processed/retry/send_batches.sh`: faz upload de cada lote, faz poll até
> `COMPLETED`, registra os `numero` que falharam e espera 150s antes do próximo.

---

## 8. Inventário (para conferir o total real no site)

A contagem no DynamoDB é de **arquivos**, não de cartas. Para conferir cartas de
verdade é preciso fazer scrape do inventário:

```bash
# dispara scrape assíncrono (pesado)
curl -s -X POST "$BASE/inventory/sync"
curl -s "$BASE/inventory/status/<job_id>"        # progresso
curl -s "$BASE/inventory/summary"                # agregados rápidos
curl -s "$BASE/inventory?colecao=DRI&tipo=normal&idioma=portugues"
curl -s "$BASE/inventory/export?colecao=DRI" -o dri_atual.csv   # baixa CSV
```

Na prática, se todos os uploads fecharam com `linhas_erro` vazio cobrindo o total
esperado, a verificação por ausência de erro já é conclusiva — o scrape é opcional.

---

## 9. Endpoints síncronos (poucas cartas, JSON)

Para ajustes pontuais sem CSV — cada um com **delay de 2s** entre cartas:
`POST /atualizar`, `POST /recadastrar`, `POST /recadastrar-massa`, `POST /excluir`.
Body: `{ "cartas": [ { numero, colecao, tipo, idioma, preco, quantidade } ] }`.

`GET /health` → sanity check da API.
