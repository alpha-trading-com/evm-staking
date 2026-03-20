# scripts/test_two_txs_one_block.py
#
# Sends TWO txs back-to-back with sequential nonces (N and N+1),
# then checks whether they landed in the same block.
#
# Notes:
# - “Same block” is not guaranteed (block producer decides), but this is the correct way to try.
# - The 2nd tx MUST use nonce N+1 (not recomputed).
# - For removeStake, `amount` is alpha-raw units (uint256) and must be <= your available stake.

import os
import sys
from pathlib import Path
import time
from web3 import Web3
from eth_account import Account
from web3.exceptions import Web3RPCError

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.interact import (  # type: ignore
    load_deployment_info,
    get_contract,
    xor_encode,
    _convert_hotkey_to_bytes32,
)

RPC_URL = os.getenv("RPC_URL", "https://test.finney.opentensor.ai/")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
HOTKEY = "5Gq2gs4ft5dhhjbHabvVbAhjMCV2RgKmVJKAFCUWiirbRT21"

NETUID = 64

# stakeLimit params (amount is rao = 1e9 per TAO)
STAKE_AMOUNT_RAO = 1000000000
# removeStake params (amount is alpha raw units; set to something you know you have)
UNSTAKE_ALPHA_RAW = 10 * 10**9

GAS = 250_000
GAS_PRICE_MULT = float(os.getenv("GAS_PRICE_MULT", "1.0"))


def _send_raw_or_reuse_hash(w3: Web3, raw_tx: bytes) -> bytes:
    """
    Send a signed raw transaction.
    If the node replies 'already known', reuse the tx hash (common when rerunning tests).
    """
    try:
        return w3.eth.send_raw_transaction(raw_tx)
    except Web3RPCError as e:
        if "already known" in str(e).lower():
            return Web3.keccak(raw_tx)
        raise


def _try_print_revert_reason(label: str, fn_call, from_addr: str, block_number: int) -> None:
    """Try to eth_call the same function to extract revert info."""
    try:
        fn_call.call({"from": from_addr}, block_identifier=block_number)
    except Exception as e:
        print(f"{label} revert reason (best-effort): {e}")


def make_w3(rpc_url: str) -> Web3:
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


def main():
    if not PRIVATE_KEY:
        raise RuntimeError("PRIVATE_KEY is required")

    w3 = make_w3(RPC_URL)
    acct = Account.from_key(PRIVATE_KEY)

    info = load_deployment_info()
    contract_address = Web3.to_checksum_address(info["contract_address"])
    contract = get_contract(w3, contract_address)

    hotkey_b32 = _convert_hotkey_to_bytes32(HOTKEY)

    base_nonce = w3.eth.get_transaction_count(acct.address, block_identifier="pending")
    gas_price = int(w3.eth.gas_price * GAS_PRICE_MULT)
    
   

    

    tx1 = contract.functions.removeStake(
        hotkey_b32,
        xor_encode(NETUID),
        xor_encode(UNSTAKE_ALPHA_RAW),
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": base_nonce,
            "gas": GAS,
            "gasPrice": gas_price,
        }
    )


    tx2 = contract.functions.stake(
        hotkey_b32,
        xor_encode(NETUID),
        xor_encode(STAKE_AMOUNT_RAO)
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": base_nonce + 1,
            "gas": GAS,
            "gasPrice": gas_price,
        }
    )
   
    tx3 = contract.functions.removeStake(
        hotkey_b32,
        xor_encode(NETUID),
        xor_encode(UNSTAKE_ALPHA_RAW),
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": base_nonce + 2,
            "gas": GAS,
            "gasPrice": gas_price,
        }
    )


    tx4 = contract.functions.stake(
        hotkey_b32,
        xor_encode(NETUID),
        xor_encode(STAKE_AMOUNT_RAO)
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": base_nonce + 3,
            "gas": GAS,
            "gasPrice": gas_price,
        }
    )
   


    signed1 = acct.sign_transaction(tx1)
    signed2 = acct.sign_transaction(tx2)
    signed3 = acct.sign_transaction(tx3)
    signed4 = acct.sign_transaction(tx4)
    # Send back-to-back (same account, sequential nonces)
    h1 = _send_raw_or_reuse_hash(w3, signed1.raw_transaction)
    h2 = _send_raw_or_reuse_hash(w3, signed2.raw_transaction)
    h3 = _send_raw_or_reuse_hash(w3, signed3.raw_transaction)
    h4 = _send_raw_or_reuse_hash(w3, signed4.raw_transaction)

    r1 = w3.eth.wait_for_transaction_receipt(h1)
    r2 = w3.eth.wait_for_transaction_receipt(h2)
    r3 = w3.eth.wait_for_transaction_receipt(h3)
    r4 = w3.eth.wait_for_transaction_receipt(h4)

    print("receipt1 block:", r1["blockNumber"], "status:", r1["status"])
    print("receipt2 block:", r2["blockNumber"], "status:", r2["status"])
    print("receipt3 block:", r3["blockNumber"], "status:", r3["status"])
    print("receipt4 block:", r4["blockNumber"], "status:", r4["status"])
    print("same_block:", r1["blockNumber"] == r2["blockNumber"])

    if r1["status"] == 0:
        _try_print_revert_reason(
            "tx1",
            contract.functions.stake(hotkey_b32, xor_encode(NETUID), xor_encode(STAKE_AMOUNT_RAO)),
            acct.address,
            r1["blockNumber"],
        )
    if r2["status"] == 0:
        _try_print_revert_reason(
            "tx2",
            contract.functions.removeStake(hotkey_b32, xor_encode(NETUID), xor_encode(UNSTAKE_ALPHA_RAW)),
            acct.address,
            r2["blockNumber"],
        )
    if r3["status"] == 0:
        _try_print_revert_reason(
            "tx3",
            contract.functions.removeStake(hotkey_b32, xor_encode(NETUID), xor_encode(UNSTAKE_ALPHA_RAW)),
            acct.address,
            r3["blockNumber"],
        )
    if r4["status"] == 0:
        _try_print_revert_reason(
            "tx4",
            contract.functions.stake(hotkey_b32, xor_encode(NETUID), xor_encode(STAKE_AMOUNT_RAO)),
            acct.address,
            r4["blockNumber"],
        )

if __name__ == "__main__":
    main()