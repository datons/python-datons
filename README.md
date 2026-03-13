# datons

Python client for [Datons](https://datons.com) data APIs.

## Installation

```bash
pip install datons
```

## Quick start

```python
from datons import Client

client = Client(token="esd_live_...")

# Query preprocessed I90 market data
df = client.esios_data.query(
    "SELECT unit, datetime, energy, price "
    "FROM operational_data_15min "
    "WHERE program = 'PDBF' AND date >= '2025-01-01' "
    "LIMIT 100"
)

# Dataset metadata (schema, programs, stats)
meta = client.esios_data.metadata()

# Search for units, companies, technologies
results = client.esios_data.search("iberdrola")
```

## Authentication

Get your API key at [datons.com/apps/esios-data](https://datons.com/apps/esios-data).

Pass it directly or set the `DATONS_API_KEY` environment variable:

```bash
export DATONS_API_KEY="esd_live_..."
```

```python
from datons import Client

client = Client()  # picks up DATONS_API_KEY
```
