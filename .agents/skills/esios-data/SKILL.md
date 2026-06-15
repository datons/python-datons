# ESIOS Data — I90 Market Data Queries

The `python-datons` library (`pip install datons`) provides SQL access to Spain's I90 electricity settlement data via a ClickHouse backend. It covers every generating unit, every market program, and every 15-minute interval since January 2023.

## Quick start

```python
from datons import Client

client = Client()  # reads API key from env, config file, or token= param
df = client.esios.query("SELECT unit, energy FROM operational_data_15min WHERE program='PDBF' LIMIT 10")
```

The client resolves the API key in this order:
1. `token=` parameter
2. `DATONS_API_KEY` environment variable
3. `~/.config/datons/config.toml` (set via `datons auth set <KEY>`)

## Available methods

| Method | Returns | Purpose |
|--------|---------|---------|
| `client.esios.query(sql)` | Polars DataFrame | Execute SQL, get a DataFrame |
| `client.esios.query(sql, backend="pandas")` | pandas DataFrame | Same, but pandas |
| `client.esios.query_raw(sql)` | `QueryResult` | Raw API response with metadata |
| `client.esios.metadata()` | `MetadataResult` | Schema, programs, date range, stats |
| `client.esios.search(q)` | `SearchResult` | Fuzzy search across units, companies, technologies |
| `client.esios.dimensions(dim)` | `DimensionResult` | List all values for a dimension (`"unit"`, `"company"`, `"technology"`) |

## Tables

### `operational_data_15min` — raw 15-minute resolution

The primary table. Every row is one unit in one program at one timestamp.

**Key columns:**

| Column | Type | Description |
|--------|------|-------------|
| `unit` | String | Unit code (e.g. `CTGN1`, `TRL1`, `PALOS2`) |
| `datetime` | DateTime (Europe/Madrid) | Period timestamp |
| `program` | String | Market program code (see below) |
| `energy` | Float64 | Energy in MWh (hourly) or MW (15-min programs) |
| `price` | Float64 | Marginal price in EUR/MWh |
| `unit_name` | String | Human-readable name (e.g. `C.N. TRILLO`) |
| `company_name` | String | Owner company |
| `technology` | String | Generation technology (e.g. `Nuclear`, `Eólica terrestre`, `Solar fotovoltaica`) |
| `sign` | String | `Subir` (up) or `Bajar` (down) — balancing programs only |
| `redispatch` | String | Redispatch mechanism — constraint programs only |
| `transaction` | String | `Mercado` or `Bilateral` — PDBF only |
| `power` | Float64 | Installed capacity in MW |

**All columns:** `unit`, `datetime`, `program`, `sign`, `redispatch`, `transaction`, `restriction`, `calculation`, `offer_type`, `session`, `offer_id`, `market_participant`, `qh_type`, `energy_sign`, `energy`, `price`, `unit_name`, `company_name`, `company_code`, `technology`, `unit_type`, `power`, `zone_regulation`, `inserted_at`

### `agg_hourly` — hourly pre-aggregation

Aggregated by hour, program, unit, sign, redispatch, session, transaction, restriction, calculation.

| Column | Type | Description |
|--------|------|-------------|
| `hour` | DateTime | Hour timestamp |
| `program` | String | Market program |
| `unit` | String | Unit code |
| `total_energy` | Float64 | Sum of energy |
| `weighted_price_sum` | Float64 | For computing weighted avg price |
| `row_count` | UInt64 | Number of underlying rows |
| `min_price` / `max_price` | Float64 | Price range |

Also retains: `sign`, `redispatch`, `session`, `transaction`, `restriction`, `calculation`.

### `agg_daily` — daily pre-aggregation

Aggregated by day, program, unit. Includes enriched dimensions.

| Column | Type | Description |
|--------|------|-------------|
| `day` | Date | Day |
| `program` | String | Market program |
| `unit` | String | Unit code |
| `technology` | String | Generation technology |
| `company_name` | String | Owner company |
| `unit_name` | String | Human-readable unit name |
| `total_energy` | Float64 | Sum of energy |
| `weighted_price_sum` | Float64 | For computing weighted avg price |
| `row_count` | UInt64 | Number of underlying rows |
| `min_price` / `max_price` | Float64 | Price range |

**Use the coarsest table that fits your query.** `agg_daily` is orders of magnitude faster for monthly/yearly analysis.

## Market programs

| Code | Name | Resolution | Description |
|------|------|-----------|-------------|
| `PDBF` | Day-ahead market | 1h | Base daily operating schedule |
| `PDVP` | Technical constraints | 1h | Constraint resolution after day-ahead |
| `PHF1`-`PHF7` | Intraday sessions 1-7 | 1h | Cumulative intraday schedule adjustments |
| `BS` | Secondary reserve (aFRR) | 15min | Reserve band assignment |
| `RTR` | Real-time constraints | 15min | Real-time redispatch |
| `RR` | Balancing market (mRR) | 15min | Replacement reserves |
| `BT` | Tertiary regulation (mFRR) | 15min | Manual frequency restoration |

## Query limits

- **Raw queries** (no aggregation): max 50 rows
- **Aggregated queries** (GROUP BY, SUM, COUNT, etc.): max 10,000 rows
- All queries are read-only with a 30-second timeout

## Example queries

### Nuclear fleet ranking (last 12 months)

```python
df = client.esios.query("""
    SELECT unit, unit_name,
           round(sum(total_energy) / 1e3, 0) AS gwh
    FROM agg_daily
    WHERE program = 'PDBF' AND technology = 'Nuclear'
      AND day BETWEEN '2024-03-01' AND '2025-02-28'
    GROUP BY unit, unit_name
    ORDER BY gwh DESC
""")
```

### Company portfolio by technology

```python
df = client.esios.query("""
    SELECT technology,
           round(sum(total_energy) / 1e3, 0) AS gwh
    FROM agg_daily
    WHERE program = 'PDBF'
      AND day BETWEEN '2024-01-01' AND '2024-12-31'
      AND company_name LIKE '%ENDESA%'
      AND technology IS NOT NULL
    GROUP BY technology
    ORDER BY gwh DESC
""")
```

### Monthly generation mix

```python
df = client.esios.query("""
    SELECT technology,
           toStartOfMonth(day) AS month,
           round(sum(total_energy) / 1e3, 0) AS gwh
    FROM agg_daily
    WHERE program = 'PDBF'
      AND day BETWEEN '2024-01-01' AND '2024-12-31'
      AND technology IN ('Eólica terrestre', 'Nuclear',
          'Solar fotovoltaica', 'Hidráulica UGH', 'Ciclo Combinado')
    GROUP BY technology, month
    ORDER BY technology, month
""")
```

### Single unit across market cascade

```python
df = client.esios.query("""
    SELECT program, round(sum(energy), 1) AS energy
    FROM operational_data_15min
    WHERE unit = 'TRL1'
      AND toStartOfHour(datetime) = toDateTime('2024-12-04 16:00:00')
    GROUP BY program
    ORDER BY program
""")
```

### PDVP curtailment by technology

```python
df = client.esios.query("""
    SELECT technology,
           round(sum(total_energy) / 1e3, 1) AS gwh
    FROM agg_daily
    WHERE program = 'PDVP'
      AND day BETWEEN '2024-01-01' AND '2024-12-31'
      AND technology IS NOT NULL
    GROUP BY technology
    ORDER BY gwh ASC
""")
```

### Find units or companies

```python
client.esios.search("trillo")     # finds TRL1, C.N. TRILLO
client.esios.search("iberdrola")  # finds company names and units
client.esios.search("solar")      # finds Solar fotovoltaica, Solar PV...
```

## Key technology names (Spanish)

Use these exact strings in WHERE clauses:
- `Nuclear`
- `Eólica terrestre` (onshore wind)
- `Solar fotovoltaica` (solar PV)
- `Hidráulica UGH` (hydro)
- `Ciclo Combinado` (combined cycle gas)
- `Gas Natural Cogeneración` (natural gas cogeneration)
- `Biomasa`
- `Solar térmica` (solar thermal)

When unsure of exact names, use `client.esios.search()` or `client.esios.dimensions("technology")`.

## Data model reference

For the complete data model, column descriptions, and categorical values, use the ESIOS Data I90 MCP server tools:
- `mcp__claude_ai_ESIOS_Data_I90__get_metadata` — full schema and program details
- `mcp__claude_ai_ESIOS_Data_I90__search` — fuzzy search across dimensions
- `mcp__claude_ai_ESIOS_Data_I90__get_dimensions` — list all values for a dimension
- `mcp__claude_ai_ESIOS_Data_I90__run_query` — execute SQL directly
