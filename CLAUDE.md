# python-datons

Python client for Datons data APIs (`pip install datons`).

## Structure

- `src/datons/client.py` — Central `Client` with shared auth and HTTP
- `src/datons/esios/` — ESIOS preprocessed data manager (first product)
- Future products go in `src/datons/<product_name>/`

## Running tests

```bash
uv run pytest
```

## Backend

The ESIOS Data API runs on droplet-ts at `~/git-repositories/mcps/esios-data/`, proxied via nginx at `mcp.datons.com/esios-data`.
