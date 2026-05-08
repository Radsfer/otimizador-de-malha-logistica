# Scripts de Dados e Execução

## 1. Gerar dataset sintético no padrão Olist

```bash
python scripts/prepare_olist_dataset.py \
    --sellers 15 \
    --customers 40 \
    --seed 2024 \
    --output-dir data_olist
```

Gera 3 CSVs no formato que o `DataLoader` consome:
- `data_olist/cds.csv` — sellers como CDs candidatos
- `data_olist/clientes.csv` — buyers como mercados de demanda
- `data_olist/produtos.csv` — categorias de produto

## 2. Validar dataset (sem OR-Tools)

```bash
python scripts/validate_dataset.py \
    --cds data_olist/cds.csv \
    --clientes data_olist/clientes.csv \
    --produtos data_olist/produtos.csv
```

Checa estrutura, coordenadas, valores negativos, e viabilidade (demanda ≤ capacidade).

## 3. Rodar otimização com dados CSV

```bash
python scripts/run_with_real_data.py \
    --cds data_olist/cds.csv \
    --clientes data_olist/clientes.csv \
    --produtos data_olist/produtos.csv \
    --tempo 120 \
    --output resultados.json
```

## 4. Usar seu próprio dataset real

Formatação dos CSVs:

**cds.csv**
```csv
id,nome,cidade,lat,lon,cacidade_total,custo_fixo_mensal,cap_P01,cap_P02,...
CD_SP,CD Guarulhos,São Paulo,-23.5505,-46.6333,25000,120000,5000,5000,...
```

**clientes.csv**
```csv
id,nome,cidade,lat,lon,demanda_P01,demanda_P02,...
CLI001,Atacadão SP,São Paulo,-23.5505,-46.6333,1200,800,...
```

**produtos.csv**
```csv
id,nome,peso_kg,valor_unitario,prazo_validade_dias,giro_classificacao
P01,Leite UHT 1L,1.05,5.99,180,A
```

### De onde vem na empresa real

| Dado | Sistema | Formato típico |
|------|---------|----------------|
| Demanda por cliente/SKU | ERP (SAP, TOTVS) | Exportação mensal de vendas faturadas |
| Localização (lat/lon) | CRM/ERP + Geocoding | Endereço → Google Maps API ou IBGE |
| Capacidade dos CDs | WMS ou planilha operacional | Unidades/dia ou pallets/dia |
| Custo fixo | Financeiro/Controladoria | DRE por centro de custo |
| Peso/valor produto | Cadastro ERP | Ficha técnica |
| Custo de frete | TMS ou tabela de transportadora | R$/ton·km |

> **Dica:** Se não tiver dados de frete, use a tabela de mercado: **R$ 0.60–1.20 / ton·km** (ajustar no `SolverSettings.custo_por_km_ton`).
