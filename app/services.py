"""Web3 connection cache, helpers, and shared services (subtensor)."""
import io
import os
import contextlib
import threading

from web3 import Web3
from eth_account import Account

import app.config  # noqa: F401 - path and env setup

import bittensor as bt
from scripts.interact import load_deployment_info, get_contract

# Reused Web3 connection; reconnects when disconnected or on connection errors.
_w3_cache: tuple | None = None
_w3_cache_lock = threading.Lock()

subtensor = bt.Subtensor(network="finney")


def clear_w3_cache() -> None:
    """Drop cached Web3 connection so next request opens a new one."""
    global _w3_cache
    with _w3_cache_lock:
        _w3_cache = None


def is_connection_error(exc: BaseException) -> bool:
    """True if the exception is likely from a lost/stale connection (e.g. WSS closed)."""
    if isinstance(exc, (ConnectionError, BrokenPipeError, OSError)):
        return True
    msg = str(exc).lower()
    return any(
        x in msg
        for x in ("connection", "closed", "broken pipe", "reset", "timeout", "websocket")
    )


def _make_w3_connection(rpc_url: str) -> Web3:
    """Create a Web3 connection (HTTP(S) or WS(S))."""
    if rpc_url.startswith(("ws://", "wss://")):
        provider = Web3.LegacyWebSocketProvider(rpc_url)
    elif rpc_url.startswith(("http://", "https://")):
        provider = Web3.HTTPProvider(rpc_url)
    else:
        raise ValueError(f"Unsupported RPC URL scheme: {rpc_url}")
    w3 = Web3(provider)
    if not w3.is_connected():
        raise RuntimeError(f"Failed to connect to {rpc_url}")
    return w3


def get_w3_account_contract():
    """Return (w3, account, contract_address, contract), reusing a cached connection when still connected."""
    global _w3_cache
    with _w3_cache_lock:
        if _w3_cache is not None:
            w3, account, contract_address, contract = _w3_cache
            try:
                if w3.is_connected():
                    return w3, account, contract_address, contract
            except Exception:
                pass
            _w3_cache = None
        rpc_url = os.getenv("RPC_URL", "https://test.finney.opentensor.ai/")
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise RuntimeError("PRIVATE_KEY is required")
        w3 = _make_w3_connection(rpc_url)
        account = Account.from_key(private_key)
        info = load_deployment_info()
        contract_address = Web3.to_checksum_address(info["contract_address"])
        contract = get_contract(w3, contract_address)
        _w3_cache = (w3, account, contract_address, contract)
    return _w3_cache


def receipt_to_dict(receipt) -> dict:
    """Convert a tx receipt to a small dict for JSON response."""
    if receipt is None:
        raise ValueError("No transaction receipt (transaction may have been sent but not confirmed)")
    h = receipt["transactionHash"]
    return {
        "transactionHash": h.hex() if hasattr(h, "hex") else str(h),
        "blockNumber": receipt["blockNumber"],
        "status": receipt["status"],
    }


def run_quiet(fn, *args, **kwargs):
    """Run fn with stdout redirected so print() from interact scripts is suppressed."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)
