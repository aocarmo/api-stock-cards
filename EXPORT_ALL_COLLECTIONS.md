# Exportar Todas as Coleções

Script para exportar **todo o inventário** em múltiplos arquivos CSV organizados por coleção, tipo e idioma.

## 🚀 Uso

```bash
python3 export_all_collections.py
```

## 📁 Estrutura de Arquivos

Cada arquivo CSV contém cartas de:
- ✅ **Uma coleção** específica (PRE, MEG, DRI, etc)
- ✅ **Um tipo** específico (normal, foil, reverse-foil)
- ✅ **Um idioma** específico (portugues, ingles, espanhol)

### Formato do nome
```
{colecao}_{tipo}_{idioma}.csv
```

### Exemplos
```
pre_normal_portugues.csv      - 128 cartas PRE normais em português
pre_foil_portugues.csv        - 55 cartas PRE foil em português
meg_normal_ingles.csv         - 49 cartas MEG normais em inglês
dri_reverse-foil_portugues.csv - 116 cartas DRI reverse-foil em português
```

## 📊 Resultado

```
📁 Diretório de saída: exports

🔍 Consultando coleções disponíveis...
📦 Coleções: PAR, PRE, PPS, PAF, PFL, DRI, MEG
🎨 Tipos: normal, foil, reverse-foil
🌍 Idiomas: portugues, ingles, espanhol

✅ pre_normal_portugues.csv                 -  128 cartas
✅ pre_foil_portugues.csv                   -   55 cartas
✅ meg_normal_ingles.csv                    -   49 cartas
...

============================================================
🎉 Exportação concluída!
📊 Total: 27 arquivos | 1200 cartas
📁 Localização: /Users/alex/Documents/projetos/pessoais/update-myp/exports
⏰ Data: 2026-02-01 22:34:45
============================================================
```

## ⚙️ Opções

### Mudar diretório de saída
```bash
python3 export_all_collections.py --output-dir meus_csvs
```

### Exportar para pasta com data
```bash
python3 export_all_collections.py --output-dir exports_$(date +%Y%m%d)
```

## 📋 Formato do CSV

Cada arquivo contém:

```csv
numero,colecao,tipo,idioma,preco,quantidade
077/131,SVI,foil,ingles,150.00,2
024/131,PRE,normal,portugues,1.99,5
```

## 🎯 Casos de Uso

### 1. Backup completo organizado
```bash
python3 export_all_collections.py --output-dir backup_$(date +%Y%m%d)
```

### 2. Análise por coleção
Cada coleção fica em arquivos separados, facilitando análise individual.

### 3. Importação seletiva
Escolha apenas os arquivos que precisa importar em outro sistema.

### 4. Compartilhamento
Envie apenas as coleções/tipos/idiomas específicos para outras pessoas.

## 📈 Estatísticas

O script mostra:
- ✅ Total de arquivos gerados
- ✅ Total de cartas exportadas
- ✅ Quantidade de cartas por arquivo
- ✅ Localização completa dos arquivos
- ✅ Data e hora da exportação

## 🔄 Atualizar Dados

Para ter dados atualizados, execute a sincronização antes:

```bash
# 1. Sincronizar inventário
curl -X POST https://018e6ro2ka.execute-api.us-east-1.amazonaws.com/dev/api/v1/inventory/sync

# 2. Aguardar ~1 minuto

# 3. Exportar tudo
python3 export_all_collections.py
```

## 📦 Arquivos Gerados

Apenas combinações que existem no inventário são exportadas. Se não há cartas foil em espanhol da coleção PRE, esse arquivo não será criado.

**Exemplo de saída:**
```
exports/
├── dri_foil_portugues.csv
├── dri_normal_ingles.csv
├── dri_normal_portugues.csv
├── dri_reverse-foil_ingles.csv
├── dri_reverse-foil_portugues.csv
├── meg_foil_ingles.csv
├── meg_foil_portugues.csv
├── meg_normal_ingles.csv
├── meg_normal_portugues.csv
├── meg_reverse-foil_ingles.csv
├── meg_reverse-foil_portugues.csv
├── paf_foil_portugues.csv
├── paf_normal_portugues.csv
├── par_normal_ingles.csv
├── pfl_foil_ingles.csv
├── pfl_foil_portugues.csv
├── pfl_normal_ingles.csv
├── pfl_normal_portugues.csv
├── pfl_reverse-foil_ingles.csv
├── pfl_reverse-foil_portugues.csv
├── pps_normal_portugues.csv
├── pre_foil_ingles.csv
├── pre_foil_portugues.csv
├── pre_normal_ingles.csv
├── pre_normal_portugues.csv
├── pre_reverse-foil_ingles.csv
└── pre_reverse-foil_portugues.csv
```

## 🆚 Diferença dos Outros Scripts

| Script | Uso | Resultado |
|--------|-----|-----------|
| `export_inventory.py` | Exportação customizada com filtros | 1 arquivo CSV |
| `export_all_collections.py` | Exportação completa organizada | Múltiplos arquivos CSV |
| API `/inventory/export` | Download direto via curl/navegador | 1 arquivo CSV |

## 💡 Dicas

1. **Organização**: Use pastas com data para manter histórico
2. **Backup**: Execute semanalmente para ter snapshots do inventário
3. **Análise**: Importe os CSVs no Excel/Google Sheets para análise
4. **Automação**: Adicione ao cron para exportação automática

```bash
# Exemplo de cron (todo domingo às 23h)
0 23 * * 0 cd /path/to/project && python3 export_all_collections.py --output-dir exports_$(date +\%Y\%m\%d)
```
