#!/usr/bin/env python3
"""
Interact with the deployed StakeWrap contract.
"""

import os
import json
import argparse
import base58
import hashlib
from web3 import Web3
from eth_account import Account
from eth_abi import encode
from eth_utils import keccak, to_hex
from dotenv import load_dotenv

# Try to import bittensor for proper SS58 decoding
try:
    import bittensor as bt
    BT_AVAILABLE = True
except ImportError:
    BT_AVAILABLE = False

load_dotenv()

# Contract ABI (minimal for interaction)
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "hotkey", "type": "bytes32"},
            {"internalType": "uint256", "name": "netuid", "type": "uint256"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "stake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "hotkey", "type": "bytes32"},
            {"internalType": "uint256", "name": "netuid", "type": "uint256"},
            {"internalType": "uint256", "name": "limitPrice", "type": "uint256"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "bool", "name": "allowPartial", "type": "bool"}
        ],
        "name": "stakeLimit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "hotkey", "type": "bytes32"},
            {"internalType": "uint256", "name": "netuid", "type": "uint256"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "removeStake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "withdraw",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "withdrawTo",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "destination_coldkey", "type": "bytes32"},
            {"internalType": "bytes32", "name": "hotkey", "type": "bytes32"},
            {"internalType": "uint256", "name": "origin_netuid", "type": "uint256"},
            {"internalType": "uint256", "name": "destination_netuid", "type": "uint256"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transferStake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "origin_hotkey", "type": "bytes32"},
            {"internalType": "bytes32", "name": "destination_hotkey", "type": "bytes32"},
            {"internalType": "uint256", "name": "origin_netuid", "type": "uint256"},
            {"internalType": "uint256", "name": "destination_netuid", "type": "uint256"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "moveStake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]


def load_deployment_info():
    """Load deployment information from deployment.json."""
    if not os.path.exists('deployment.json'):
        raise FileNotFoundError(
            "deployment.json not found. Please deploy the contract first."
        )
    
    with open('deployment.json', 'r') as f:
        return json.load(f)


def get_contract(w3, contract_address, abi=None):
    """Get contract instance."""
    if abi is None:
        # Try to load full ABI from artifacts first
        artifact_path = 'artifacts/contracts/StakeWrap.sol/StakeWrap.json'
        if os.path.exists(artifact_path):
            try:
                with open(artifact_path, 'r') as f:
                    artifact = json.load(f)
                    abi = artifact['abi']
            except:
                abi = CONTRACT_ABI
        else:
            abi = CONTRACT_ABI
    return w3.eth.contract(address=contract_address, abi=abi)


def ss58_to_bytes32(ss58_address):
    """
    Convert SS58 address to bytes32.
    
    Args:
        ss58_address: SS58 encoded address string
    
    Returns:
        bytes32 representation of the address
    """
    try:
        # Use bittensor library if available for proper decoding
        if BT_AVAILABLE:
            try:
                # Decode SS58 using bittensor's utility
                decoded_bytes = bt.utils.ss58_address_to_bytes(ss58_address)
                # Ensure it's exactly 32 bytes
                if len(decoded_bytes) == 32:
                    return decoded_bytes
                elif len(decoded_bytes) < 32:
                    # Pad with zeros if needed
                    return decoded_bytes + b'\x00' * (32 - len(decoded_bytes))
                else:
                    # Take first 32 bytes if longer
                    return decoded_bytes[:32]
            except Exception as bt_error:
                print(f"Warning: Bittensor library decode failed: {bt_error}, trying manual decode...")
        
        # Fallback: Manual SS58 decoding
        decoded = base58.b58decode(ss58_address)
        
        if len(decoded) < 2:
            raise ValueError("Invalid SS58 address: too short")
        
        # SS58 format: [prefix_bytes][address_bytes][checksum_bytes]
        # For Bittensor hotkeys: prefix is 1 byte (42), address is 32 bytes, checksum is 2 bytes
        # Total: 1 + 32 + 2 = 35 bytes
        
        if len(decoded) == 35:
            # Standard format: 1 byte prefix + 32 bytes address + 2 bytes checksum
            address_bytes = decoded[1:33]
        elif len(decoded) == 34:
            # Possibly: 1 byte prefix + 32 bytes address + 1 byte checksum
            address_bytes = decoded[1:33]
        elif len(decoded) == 33:
            # Possibly: 1 byte prefix + 32 bytes address
            address_bytes = decoded[1:]
        elif len(decoded) > 35:
            # Longer format, try to extract 32 bytes after prefix
            # Assume 1-2 byte prefix
            if decoded[0] < 64:
                prefix_len = 1
            else:
                prefix_len = 2
            address_bytes = decoded[prefix_len:prefix_len+32]
        else:
            raise ValueError(f"Unexpected SS58 decoded length: {len(decoded)}")
        
        # Ensure we have exactly 32 bytes
        if len(address_bytes) != 32:
            if len(address_bytes) < 32:
                address_bytes = address_bytes + b'\x00' * (32 - len(address_bytes))
            else:
                address_bytes = address_bytes[:32]
        
        return address_bytes
    except Exception as e:
        raise ValueError(f"Failed to decode SS58 address '{ss58_address}': {e}")


def stake(w3, account, contract_address, hotkey, netuid, amount):
    """Stake tokens."""
    contract = get_contract(w3, contract_address)
    
    # Check contract balance - the precompile checks the contract's balance
    contract_balance = w3.eth.get_balance(contract_address)
    print(f"Contract balance: {Web3.from_wei(contract_balance, 'ether')} TAO ({contract_balance} rao)")
    print(f"Staking amount: {Web3.from_wei(amount, 'ether')} TAO ({amount} rao)")
    
    if contract_balance < amount:
        print(f"\n❌ ERROR: Contract balance ({Web3.from_wei(contract_balance, 'ether')} TAO) is insufficient!")
        print(f"   The precompile checks the contract's TAO balance, not your account balance.")
        print(f"   You need to send {Web3.from_wei(amount, 'ether')} TAO to the contract first.")
        print(f"\n   To send TAO to the contract, use:")
        print(f"   Send {Web3.from_wei(amount, 'ether')} TAO to: {contract_address}")
        print(f"   Or use a wallet/exchange to send TAO to this address.")
        raise ValueError(f"Insufficient contract balance: need {amount} rao, have {contract_balance} rao")
    
    # Convert hotkey string to bytes32
    if isinstance(hotkey, str):
        # Check if it's SS58 format (starts with 5 and is base58)
        if hotkey.startswith('5') and len(hotkey) > 40:
            try:
                hotkey_bytes = ss58_to_bytes32(hotkey)
                print(f"Converted SS58 hotkey {hotkey} to bytes32: {hotkey_bytes.hex()}")
            except Exception as e:
                raise ValueError(f"Failed to convert SS58 hotkey: {e}")
        # Check if it's hex format (0x... or just hex)
        elif hotkey.startswith('0x') or all(c in '0123456789abcdefABCDEF' for c in hotkey.replace('0x', '')):
            hotkey_bytes = bytes.fromhex(hotkey.replace('0x', ''))
            if len(hotkey_bytes) != 32:
                raise ValueError("Hotkey must be 32 bytes (64 hex characters)")
        else:
            raise ValueError("Hotkey must be either SS58 format or 32-byte hex string")
        hotkey = hotkey_bytes
    
    print(f"Staking {Web3.from_wei(amount, 'ether')} TAO to netuid {netuid}")
    print(f"Hotkey (bytes32): 0x{hotkey.hex()}")
    # Build transaction - amount is already in rao
    tx = contract.functions.stake(
        hotkey,
        netuid,
        amount  # Amount is already in rao
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    
    # Sign and send
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Stake transaction hash: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block: {receipt.blockNumber}")
    
    # Check if transaction succeeded
    if receipt.status == 0:
        print("❌ Transaction failed!")
        # Try to get revert reason
        try:
            # Try to call the function to see the revert reason
            contract.functions.stake(hotkey, netuid, amount).call({'from': account.address})
        except Exception as revert_error:
            error_msg = str(revert_error)
            if "execution reverted" in error_msg.lower():
                if ":" in error_msg:
                    revert_reason = error_msg.split(":", 1)[1].strip()
                    print(f"Revert reason: {revert_reason}")
                else:
                    print("Transaction reverted (reason not available)")
                    print(f"Full error: {error_msg}")
            else:
                print(f"Error: {error_msg}")
        return receipt
    
    print("✅ Stake transaction successful!")
    return receipt


def stake_limit(w3, account, contract_address, hotkey, netuid, limit_price, amount, allow_partial):
    """Stake with limit price."""
    contract = get_contract(w3, contract_address)
    
    # Convert hotkey string to bytes32
    if isinstance(hotkey, str):
        # Check if it's SS58 format (starts with 5 and is base58)
        if hotkey.startswith('5') and len(hotkey) > 40:
            try:
                hotkey_bytes = ss58_to_bytes32(hotkey)
                print(f"Converted SS58 hotkey {hotkey} to bytes32: {hotkey_bytes.hex()}")
            except Exception as e:
                raise ValueError(f"Failed to convert SS58 hotkey: {e}")
        # Check if it's hex format (0x... or just hex)
        elif hotkey.startswith('0x') or all(c in '0123456789abcdefABCDEF' for c in hotkey.replace('0x', '')):
            hotkey_bytes = bytes.fromhex(hotkey.replace('0x', ''))
            if len(hotkey_bytes) != 32:
                raise ValueError("Hotkey must be 32 bytes (64 hex characters)")
        else:
            raise ValueError("Hotkey must be either SS58 format or 32-byte hex string")
        hotkey = hotkey_bytes
    
    # Build transaction
    tx = contract.functions.stakeLimit(
        hotkey,
        netuid,
        limit_price,
        amount,
        allow_partial
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    
    # Sign and send
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"StakeLimit transaction hash: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block: {receipt.blockNumber}")
    return receipt


def remove_stake(w3, account, contract_address, hotkey, netuid, amount):
    """
    Remove stake (unstake alpha tokens).
    
    Note: amount is in ALPHA tokens, not TAO/rao!
    The precompile converts alpha back to TAO when unstaking.
    """
    contract = get_contract(w3, contract_address)
    
    # Convert hotkey string to bytes32
    if isinstance(hotkey, str):
        # Check if it's SS58 format (starts with 5 and is base58)
        if hotkey.startswith('5') and len(hotkey) > 40:
            try:
                hotkey_bytes = ss58_to_bytes32(hotkey)
                print(f"Converted SS58 hotkey {hotkey} to bytes32: {hotkey_bytes.hex()}")
            except Exception as e:
                raise ValueError(f"Failed to convert SS58 hotkey: {e}")
        # Check if it's hex format (0x... or just hex)
        elif hotkey.startswith('0x') or all(c in '0123456789abcdefABCDEF' for c in hotkey.replace('0x', '')):
            hotkey_bytes = bytes.fromhex(hotkey.replace('0x', ''))
            if len(hotkey_bytes) != 32:
                raise ValueError("Hotkey must be 32 bytes (64 hex characters)")
        else:
            raise ValueError("Hotkey must be either SS58 format or 32-byte hex string")
        hotkey = hotkey_bytes
    
    print(f"Unstaking {amount} ALPHA tokens from netuid {netuid}")
    print(f"Hotkey (bytes32): 0x{hotkey.hex()}")
    print(f"⚠️  Note: Amount is in ALPHA tokens, not TAO!")
    
    # Build transaction - amount is in alpha (not rao!)
    tx = contract.functions.removeStake(
        hotkey,
        netuid,
        amount  # Amount is in alpha tokens
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    
    # Sign and send
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"RemoveStake transaction hash: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block: {receipt.blockNumber}")
    return receipt


def withdraw(w3, account, contract_address, amount=None):
    """Withdraw TAO from the contract."""
    # Load full ABI from artifacts to ensure we have the correct function signatures
    artifact_path = 'artifacts/contracts/StakeWrap.sol/StakeWrap.json'
    if os.path.exists(artifact_path):
        with open(artifact_path, 'r') as f:
            artifact = json.load(f)
            full_abi = artifact['abi']
        contract = w3.eth.contract(address=contract_address, abi=full_abi)
    else:
        contract = get_contract(w3, contract_address)
    
    # Verify ownership before attempting withdrawal
    try:
        owner = contract.functions.owner().call()
        if owner.lower() != account.address.lower():
            print(f"❌ ERROR: You are not the contract owner!")
            print(f"   Contract owner: {owner}")
            print(f"   Your account: {account.address}")
            print(f"   You must use the owner's private key to withdraw")
            return None
        print(f"✅ Verified: You are the contract owner")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify ownership: {e}")
    
    # Check if withdraw function exists on the deployed contract
    try:
        # Try to get the function code - if it doesn't exist, this will help us detect it
        if amount is None:
            # Try a static call to see if function exists
            try:
                contract.functions.withdraw().call({'from': account.address, 'gas': 100000})
            except Exception as call_err:
                if "execution reverted" not in str(call_err).lower():
                    # If it's not a revert, the function might not exist
                    pass
    except:
        pass
    
    # Check contract balance
    balance = w3.eth.get_balance(contract_address)
    print(f"Contract balance: {Web3.from_wei(balance, 'ether')} TAO ({balance} rao)")
    
    if balance == 0:
        print("No funds to withdraw")
        return None
    
    # Build transaction - use the ABI method first
    try:
        if amount is None:
            # Withdraw all - call withdraw() with no parameters
            tx = contract.functions.withdraw().build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
            })
        else:
            # Withdraw specific amount - call withdraw(uint256) with one parameter
            if amount > balance:
                raise ValueError(f"Amount ({amount} rao) exceeds contract balance ({balance} rao)")
            tx = contract.functions.withdraw(amount).build_transaction({
                'from': account.address,
                'nonce': w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': w3.eth.gas_price,
            })
    except Exception as e:
        error_str = str(e)
        if "was not found" in error_str or "not found" in error_str.lower():
            print(f"❌ ERROR: The withdraw function is not available on the deployed contract!")
            print(f"   This contract was deployed before the withdraw functions were added.")
            print(f"   You need to redeploy the contract with the updated code.")
            print(f"   Run: python scripts/deploy.py")
            return None
        print(f"Error building transaction: {e}")
        print("Trying alternative method using function selector...")
        # Fallback: use function selector directly
        if amount is None:
            # withdraw() function selector: keccak256("withdraw()")[:4]
            func_selector = keccak(b"withdraw()")[:4]
            data = to_hex(func_selector)
        else:
            # withdraw(uint256) function selector: keccak256("withdraw(uint256)")[:4]
            func_selector = keccak(b"withdraw(uint256)")[:4]
            encoded_params = encode(['uint256'], [amount])
            data = to_hex(func_selector + encoded_params)
        
        tx = {
            'to': contract_address,
            'from': account.address,
            'data': data,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
        }
    
    # Sign and send
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Withdraw transaction hash: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block: {receipt.blockNumber}")
    
    # Check if transaction succeeded
    if receipt.status == 0:
        print("❌ Transaction failed!")
        # Try to get revert reason
        try:
            # Try to call the function to see the revert reason
            if amount is None:
                contract.functions.withdraw().call({'from': account.address})
            else:
                contract.functions.withdraw(amount).call({'from': account.address})
        except Exception as revert_error:
            error_msg = str(revert_error)
            if "execution reverted" in error_msg:
                # Extract revert reason if available
                if ":" in error_msg:
                    revert_reason = error_msg.split(":", 1)[1].strip()
                    print(f"Revert reason: {revert_reason}")
                else:
                    print("Transaction reverted (reason not available)")
            else:
                print(f"Error: {error_msg}")
        except:
            print("Transaction reverted. Could not decode revert reason.")
        return receipt
    
    # Check final balance
    final_balance = w3.eth.get_balance(contract_address)
    print(f"Contract balance after withdrawal: {Web3.from_wei(final_balance, 'ether')} TAO ({final_balance} rao)")
    
    return receipt


def withdraw_to(w3, account, contract_address, to_address, amount):
    """Withdraw TAO from the contract to a specific address."""
    contract = get_contract(w3, contract_address)
    
    # Check contract balance
    balance = w3.eth.get_balance(contract_address)
    print(f"Contract balance: {Web3.from_wei(balance, 'ether')} TAO")
    
    if amount > balance:
        raise ValueError(f"Amount ({amount} rao) exceeds contract balance ({balance} rao)")
    
    # Validate recipient address
    to_address = Web3.to_checksum_address(to_address)
    
    # Build transaction
    tx = contract.functions.withdrawTo(to_address, amount).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
    })
    
    # Sign and send
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"WithdrawTo transaction hash: {tx_hash.hex()}")
    print(f"Withdrawing {Web3.from_wei(amount, 'ether')} TAO to {to_address}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block: {receipt.blockNumber}")
    return receipt


def transfer_stake(w3, account, contract_address, destination_coldkey, hotkey, origin_netuid, destination_netuid, amount):
    """
    Transfer stake (alpha) to another coldkey.
    
    This allows transferring alpha tokens to another account's coldkey.
    """
    contract = get_contract(w3, contract_address)
    
    # Convert hotkey and coldkey strings to bytes32
    if isinstance(hotkey, str):
        if hotkey.startswith('5') and len(hotkey) > 40:
            try:
                hotkey_bytes = ss58_to_bytes32(hotkey)
                print(f"Converted SS58 hotkey {hotkey} to bytes32: {hotkey_bytes.hex()}")
            except Exception as e:
                raise ValueError(f"Failed to convert SS58 hotkey: {e}")
        elif hotkey.startswith('0x') or all(c in '0123456789abcdefABCDEF' for c in hotkey.replace('0x', '')):
            hotkey_bytes = bytes.fromhex(hotkey.replace('0x', ''))
            if len(hotkey_bytes) != 32:
                raise ValueError("Hotkey must be 32 bytes (64 hex characters)")
        else:
            raise ValueError("Hotkey must be either SS58 format or 32-byte hex string")
        hotkey = hotkey_bytes
    
    if isinstance(destination_coldkey, str):
        if destination_coldkey.startswith('5') and len(destination_coldkey) > 40:
            try:
                coldkey_bytes = ss58_to_bytes32(destination_coldkey)
                print(f"Converted SS58 coldkey {destination_coldkey} to bytes32: {coldkey_bytes.hex()}")
            except Exception as e:
                raise ValueError(f"Failed to convert SS58 coldkey: {e}")
        elif destination_coldkey.startswith('0x') or all(c in '0123456789abcdefABCDEF' for c in destination_coldkey.replace('0x', '')):
            coldkey_bytes = bytes.fromhex(destination_coldkey.replace('0x', ''))
            if len(coldkey_bytes) != 32:
                raise ValueError("Coldkey must be 32 bytes (64 hex characters)")
        else:
            raise ValueError("Coldkey must be either SS58 format or 32-byte hex string")
        destination_coldkey = coldkey_bytes
    
    print(f"Transferring {Web3.from_wei(amount, 'ether')} TAO worth of stake (alpha)")
    print(f"From netuid {origin_netuid} to netuid {destination_netuid}")
    print(f"Hotkey (bytes32): 0x{hotkey.hex()}")
    print(f"Destination coldkey (bytes32): 0x{destination_coldkey.hex()}")
    
    # Build transaction
    tx = contract.functions.transferStake(
        destination_coldkey,
        hotkey,
        origin_netuid,
        destination_netuid,
        amount  # Amount in rao
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    
    # Sign and send
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"TransferStake transaction hash: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block: {receipt.blockNumber}")
    return receipt


def move_stake(w3, account, contract_address, origin_hotkey, destination_hotkey, origin_netuid, destination_netuid, amount):
    """
    Move stake from one hotkey to another.
    
    This moves stake (alpha) between different hotkeys.
    """
    contract = get_contract(w3, contract_address)
    
    # Convert hotkey strings to bytes32
    def convert_hotkey(hotkey_str, name):
        if isinstance(hotkey_str, str):
            if hotkey_str.startswith('5') and len(hotkey_str) > 40:
                try:
                    hotkey_bytes = ss58_to_bytes32(hotkey_str)
                    print(f"Converted SS58 {name} {hotkey_str} to bytes32: {hotkey_bytes.hex()}")
                except Exception as e:
                    raise ValueError(f"Failed to convert SS58 {name}: {e}")
            elif hotkey_str.startswith('0x') or all(c in '0123456789abcdefABCDEF' for c in hotkey_str.replace('0x', '')):
                hotkey_bytes = bytes.fromhex(hotkey_str.replace('0x', ''))
                if len(hotkey_bytes) != 32:
                    raise ValueError(f"{name} must be 32 bytes (64 hex characters)")
            else:
                raise ValueError(f"{name} must be either SS58 format or 32-byte hex string")
            return hotkey_bytes
        return hotkey_str
    
    origin_hotkey = convert_hotkey(origin_hotkey, "origin_hotkey")
    destination_hotkey = convert_hotkey(destination_hotkey, "destination_hotkey")
    
    print(f"Moving {Web3.from_wei(amount, 'ether')} TAO worth of stake")
    print(f"From hotkey 0x{origin_hotkey.hex()} (netuid {origin_netuid})")
    print(f"To hotkey 0x{destination_hotkey.hex()} (netuid {destination_netuid})")
    
    # Build transaction
    tx = contract.functions.moveStake(
        origin_hotkey,
        destination_hotkey,
        origin_netuid,
        destination_netuid,
        amount  # Amount in rao
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    
    # Sign and send
    signed_txn = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"MoveStake transaction hash: {tx_hash.hex()}")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction confirmed in block: {receipt.blockNumber}")
    return receipt


def main():
    parser = argparse.ArgumentParser(description='Interact with StakeWrap contract')
    parser.add_argument('action', choices=['stake', 'stakeLimit', 'removeStake', 'transferStake', 'moveStake', 'owner', 'withdraw', 'withdrawTo', 'balance'],
                       help='Action to perform')
    parser.add_argument('--hotkey', type=str, help='Hotkey (SS58 or 32 bytes hex string)')
    parser.add_argument('--origin-hotkey', type=str, help='Origin hotkey for moveStake (SS58 or 32 bytes hex string)')
    parser.add_argument('--destination-hotkey', type=str, help='Destination hotkey for moveStake (SS58 or 32 bytes hex string)')
    parser.add_argument('--destination-coldkey', type=str, help='Destination coldkey for transferStake (SS58 or 32 bytes hex string)')
    parser.add_argument('--netuid', type=int, help='Network UID')
    parser.add_argument('--origin-netuid', type=int, help='Origin netuid for transferStake/moveStake')
    parser.add_argument('--destination-netuid', type=int, help='Destination netuid for transferStake/moveStake')
    parser.add_argument('--amount', type=float, help='Amount: TAO for stake/transferStake/moveStake, ALPHA for removeStake, TAO for withdraw')
    parser.add_argument('--limit-price', type=int, dest='limit_price',
                       help='Limit price for stakeLimit')
    parser.add_argument('--allow-partial', action='store_true',
                       help='Allow partial fill for stakeLimit')
    parser.add_argument('--contract', type=str, help='Contract address (overrides deployment.json)')
    parser.add_argument('--to', type=str, help='Recipient address for withdrawTo')
    
    args = parser.parse_args()
    
    # Load environment variables
    rpc_url = os.getenv('RPC_URL', 'https://test.finney.opentensor.ai/')
    private_key = os.getenv('PRIVATE_KEY')
    
    if not private_key:
        raise ValueError("PRIVATE_KEY environment variable is required")
    
    # Connect to blockchain
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError(f"Failed to connect to {rpc_url}")
    
    # Load account
    account = Account.from_key(private_key)
    
    # Get contract address
    if args.contract:
        contract_address = Web3.to_checksum_address(args.contract)
    else:
        deployment_info = load_deployment_info()
        contract_address = Web3.to_checksum_address(deployment_info['contract_address'])
    
    print(f"Contract address: {contract_address}")
    print(f"Account: {account.address}")
    
    # Execute action
    if args.action == 'owner':
        contract = get_contract(w3, contract_address)
        owner = contract.functions.owner().call()
        print(f"Contract owner: {owner}")
        print(f"Your account: {account.address}")
        if owner.lower() == account.address.lower():
            print("✅ You are the contract owner")
        else:
            print("❌ You are NOT the contract owner")
            print("   You need to use the owner's private key to withdraw")
    
    elif args.action == 'balance':
        balance = w3.eth.get_balance(contract_address)
        print(f"Contract balance: {Web3.from_wei(balance, 'ether')} TAO ({balance} rao)")
    
    elif args.action == 'stake':
        if not all([args.hotkey, args.netuid is not None, args.amount is not None]):
            parser.error("stake requires --hotkey, --netuid, and --amount")
        # Convert TAO to rao
        amount_rao = int(args.amount * 10**18)
        stake(w3, account, contract_address, args.hotkey, args.netuid, amount_rao)
    
    elif args.action == 'stakeLimit':
        if not all([args.hotkey, args.netuid is not None, args.limit_price is not None,
                   args.amount is not None]):
            parser.error("stakeLimit requires --hotkey, --netuid, --limit-price, and --amount")
        # Convert TAO to rao
        amount_rao = int(args.amount * 10**18)
        stake_limit(w3, account, contract_address, args.hotkey, args.netuid,
                   args.limit_price, amount_rao, args.allow_partial)
    
    elif args.action == 'removeStake':
        if not all([args.hotkey, args.netuid is not None, args.amount is not None]):
            parser.error("removeStake requires --hotkey, --netuid, and --amount")
        # Amount is in ALPHA tokens (not TAO!)
        # User provides alpha amount directly (no conversion needed)
        amount_alpha = int(args.amount)
        print(f"⚠️  Note: removeStake amount is in ALPHA tokens, not TAO!")
        print(f"   You specified: {amount_alpha} ALPHA")
        remove_stake(w3, account, contract_address, args.hotkey, args.netuid, amount_alpha)
    
    elif args.action == 'transferStake':
        if not all([args.destination_coldkey, args.hotkey, args.origin_netuid is not None, 
                   args.destination_netuid is not None, args.amount is not None]):
            parser.error("transferStake requires --destination-coldkey, --hotkey, --origin-netuid, --destination-netuid, and --amount")
        # Convert TAO to rao
        amount_rao = int(args.amount * 10**18)
        transfer_stake(w3, account, contract_address, args.destination_coldkey, args.hotkey,
                       args.origin_netuid, args.destination_netuid, amount_rao)
    
    elif args.action == 'moveStake':
        if not all([args.origin_hotkey, args.destination_hotkey, args.origin_netuid is not None,
                   args.destination_netuid is not None, args.amount is not None]):
            parser.error("moveStake requires --origin-hotkey, --destination-hotkey, --origin-netuid, --destination-netuid, and --amount")
        # Convert TAO to rao
        amount_rao = int(args.amount * 10**18)
        move_stake(w3, account, contract_address, args.origin_hotkey, args.destination_hotkey,
                  args.origin_netuid, args.destination_netuid, amount_rao)
    
    elif args.action == 'withdraw':
        # Convert TAO to rao if amount is provided
        amount_rao = int(args.amount * 10**18) if args.amount is not None else None
        withdraw(w3, account, contract_address, amount_rao)
    
    elif args.action == 'withdrawTo':
        if not all([args.to, args.amount is not None]):
            parser.error("withdrawTo requires --to and --amount")
        # Convert TAO to rao
        amount_rao = int(args.amount * 10**18)
        withdraw_to(w3, account, contract_address, args.to, amount_rao)


if __name__ == '__main__':
    main()

