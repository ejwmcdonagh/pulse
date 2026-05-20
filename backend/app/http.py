import certifi
import httpx


def async_client(**kwargs) -> httpx.AsyncClient:
    """
    httpx client with certifi's CA bundle explicitly set.
    Required on macOS Homebrew Python, which doesn't trust the system cert store.
    """
    return httpx.AsyncClient(verify=certifi.where(), **kwargs)
