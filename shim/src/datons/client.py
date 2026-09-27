"""Legacy endpoint compatibility backed by the canonical Joltio client."""
import os
from joltio.client import Client as JoltioClient
from joltio.exceptions import DatonsError

class Client(JoltioClient):
    def __init__(self, token=None, *, base_url="https://api.datons.com", timeout=30.0):
        from datons.config import read_api_key
        key = token or os.getenv("DATONS_API_KEY") or read_api_key()
        if not key:
            raise DatonsError("API key required. Set DATONS_API_KEY or migrate to JOLTIO_API_KEY.")
        super().__init__(api_key=key, base_url=base_url, timeout=timeout)

    def _request(self, method, path, params=None, json=None):
        if path.startswith('/data/'):
            path = '/esios-data/' + path.removeprefix('/data/')
        return super()._request(method, path, params=params, json=json)
