import os
import sys
import time
import threading
from pathlib import Path

import bittensor as bt
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

# Ensure repo root is on path and load .env
_REPO_ROOT = Path(__file__).resolve().parent
load_dotenv(_REPO_ROOT / ".env")
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
os.chdir(_REPO_ROOT)

from scripts.interact import stake_limit, load_deployment_info
from utils.tolerance import calculate_stake_limit_price

NETWORK = "finney"
COLDKEY_SWAP_EVENT_TYPE = "COLDKEY_SWAP"
IDENTITY_CHANGE_EVENT_TYPE = "IDENTITY_CHANGE"
COLDKEY_SWAP_FINISHED_EVENT_TYPE = "COLDKEY_SWAP_FINISHED"
DEREGISTERED_EVENT_TYPE = "DEREGISTERED"

# When coldkey swap is scheduled for these netuids, auto-stake 127 TAO with min_tolerance
AUTO_STAKE_NETUIDS = (28, 40, 57)
AUTO_STAKE_TAO = 127.0
AUTO_STAKE_MIN_TOLERANCE = True
DEFAULT_HOTKEY = "5Gq2gs4ft5dhhjbHabvVbAhjMCV2RgKmVJKAFCUWiirbRT21"


def _make_w3_connection(rpc_url: str) -> Web3:
    """Create a Web3 connection that supports both HTTP(S) and WS(S) RPC URLs."""
    if rpc_url.startswith(("ws://", "wss://")):
        provider = Web3.WebsocketProvider(rpc_url)
    elif rpc_url.startswith(("http://", "https://")):
        provider = Web3.HTTPProvider(rpc_url)
    else:
        raise ValueError(f"Unsupported RPC URL scheme: {rpc_url}")

    w3 = Web3(provider)
    if not w3.is_connected():
        raise RuntimeError(f"Failed to connect to {rpc_url}")
    return w3


def _get_w3_account_contract():
    rpc_url = os.getenv("RPC_URL", "https://test.finney.opentensor.ai/")
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        raise RuntimeError("PRIVATE_KEY is required for auto-stake")
    w3 = _make_w3_connection(rpc_url)
    account = Account.from_key(private_key)
    info = load_deployment_info()
    contract_address = Web3.to_checksum_address(info["contract_address"])
    return w3, account, contract_address


def _run_auto_stake_for_netuid(subtensor: bt.Subtensor, netuid: int):
    """Stake AUTO_STAKE_TAO on netuid with min_tolerance (stakeLimit). Runs in thread."""
    hotkey = os.getenv("HOTKEY", DEFAULT_HOTKEY)
    try:
        w3, account, contract_address = _get_w3_account_contract()
    except Exception as e:
        print(f"Auto-stake netuid {netuid}: skipped – {e}")
        return
    amount_rao = int(AUTO_STAKE_TAO * 10**9)
    try:
        limit_price = int(calculate_stake_limit_price(
            tao_amount=AUTO_STAKE_TAO,
            netuid=netuid,
            min_tolerance_staking=AUTO_STAKE_MIN_TOLERANCE,
            default_rate_tolerance=0.5,
            subtensor=subtensor,
        ))
        receipt = stake_limit(
            w3, account, contract_address,
            hotkey, netuid, limit_price, amount_rao, allow_partial=False,
        )
        msg = f"Auto-stake subnet {netuid}: {AUTO_STAKE_TAO} TAO (min_tolerance) – tx {receipt['transactionHash'].hex()}"
        print(msg)
    except Exception as e:
        print(f"Auto-stake netuid {netuid} failed: {e}")


class ColdkeySwapFetcher:
    def __init__(self):
        self.subtensor = bt.Subtensor(NETWORK)
        self.subtensor_finney = bt.Subtensor("finney")

        self.last_checked_block = self.subtensor.get_current_block()
        self.subnet_names = []
        self.owner_coldkeys = []
        
  
    def fetch_extrinsic_data(self, block_number):
        """Extract ColdkeySwapScheduled events from the data"""
        events = []
        print(f"Fetching events from chain")
        block_hash = self.subtensor.substrate.get_block_hash(block_id=block_number)
        extrinsics = self.subtensor.substrate.get_extrinsics(block_hash=block_hash)
        subnet_infos = self.subtensor.all_subnets()
        owner_coldkeys = [subnet_info.owner_coldkey for subnet_info in subnet_infos]
        subnet_names = [subnet_info.subnet_name for subnet_info in subnet_infos]
        print(f"Fetched {len(extrinsics)} events from chain and {len(subnet_infos)} subnets")

        for ex in extrinsics:
            call = ex.value.get('call', {})
            if (
                call.get('call_module') == 'SubtensorModule' and
                call.get('call_function') == 'schedule_swap_coldkey'
            ):
                # Get the new coldkey from call_args
                args = call.get('call_args', [])
                new_coldkey = next((a['value'] for a in args if a['name'] == 'new_coldkey'), None)
                from_coldkey = ex.value.get('address', None)
                print(f"Swap scheduled: from {from_coldkey} to {new_coldkey}")
                
                try:
                    subnet_id = owner_coldkeys.index(from_coldkey)
                    event_info = {
                        'event_type': COLDKEY_SWAP_EVENT_TYPE,
                        'old_coldkey': from_coldkey,
                        'new_coldkey': new_coldkey,
                        'subnet': subnet_id,
                    }
                    
                    events.append(event_info)
                except ValueError:
                    print(f"From coldkey {from_coldkey} not found in owner coldkeys")

            if (
                call.get('call_module') == 'SubtensorModule' and
                call.get('call_function') == 'set_subnet_identity'
            ):
                
                # Get the new coldkey from call_args
                address = ex.value.get('address', None)
                # To get the old identity, use the current subnet identity from subnet_infos[subnet_id].
                # To get the new identity, get from call_args['subnet_name'].
                try:
                    subnet_id = owner_coldkeys.index(address)
                    old_identity = subnet_infos[subnet_id].subnet_name
                    call_args = call.get('call_args', [])
                    new_identity = next((a['value'] for a in call_args if a['name'] == 'subnet_name'), None)
                    
                    event_info = {
                        'event_type': IDENTITY_CHANGE_EVENT_TYPE,
                        'subnet': subnet_id,
                        'old_identity': old_identity,
                        'new_identity': new_identity,
                    }
                    events.append(event_info)
                except ValueError:
                    print(f"Address {address} not found in owner coldkeys")

        for i in range(len(self.subnet_names)):
            if self.owner_coldkeys[i] != owner_coldkeys[i]:
                if self.subnet_names[i] != subnet_names[i]:
                    event_info = {
                        'event_type': DEREGISTERED_EVENT_TYPE,
                        'subnet': i,
                        'coldkey': owner_coldkeys[i],
                    }
                    events.append(event_info)
                else:
                    event_info = {
                        'event_type': COLDKEY_SWAP_FINISHED_EVENT_TYPE,
                        'subnet': i,
                    }
                    events.append(event_info)

        self.subnet_names = subnet_names
        self.owner_coldkeys = owner_coldkeys
        return events
 
    def run(self):
        while True:
            current_block = self.subtensor.get_current_block()
            print(f"Current block: {current_block}")
            if current_block < self.last_checked_block:
                time.sleep(2)
                continue

            print(f"Fetching coldkey swaps for block {self.last_checked_block}")
            while True:
                try:
                    events = self.fetch_extrinsic_data(self.last_checked_block)
                    if len(events) > 0:
                        try:
                            # When coldkey swap scheduled for 28, 40, 57: stake 127 TAO with min_tolerance
                            for ev in events:
                                if ev.get("event_type") == COLDKEY_SWAP_EVENT_TYPE and ev.get("subnet") in AUTO_STAKE_NETUIDS:
                                    netuid = ev["subnet"]
                                    _run_auto_stake_for_netuid(self.subtensor, netuid)
                        except Exception as e:
                            print(f"Error sending message: {e}")
                    else:
                        print("No coldkey swaps found")
                    
                    self.last_checked_block += 1
                    break

                except Exception as e:
                    print(f"Error fetching coldkey swaps: {e}")
                    time.sleep(1)



if __name__ == "__main__":
    fetcher = ColdkeySwapFetcher()
    fetcher.run()