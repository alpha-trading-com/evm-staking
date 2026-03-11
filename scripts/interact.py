#!/usr/bin/env python3
"""
Interact with the deployed StakeWrap contract.
"""

import os
import json
import argparse
from web3 import Web3
from eth_account import Account
from eth_abi import encode
from eth_utils import keccak, to_hex
from dotenv import load_dotenv

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


def stake(w3, account, contract_address, hotkey, netuid, amount):
    """Stake tokens."""
    contract = get_contract(w3, contract_address)
    
    # Convert hotkey string to bytes32
    if isinstance(hotkey, str):
        hotkey_bytes = bytes.fromhex(hotkey.replace('0x', ''))
        if len(hotkey_bytes) != 32:
            raise ValueError("Hotkey must be 32 bytes (64 hex characters)")
        hotkey = hotkey_bytes
    
    # Build transaction
    tx = contract.functions.stake(
        hotkey,
        netuid,
        amount
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
    return receipt


def stake_limit(w3, account, contract_address, hotkey, netuid, limit_price, amount, allow_partial):
    """Stake with limit price."""
    contract = get_contract(w3, contract_address)
    
    # Convert hotkey string to bytes32
    if isinstance(hotkey, str):
        hotkey_bytes = bytes.fromhex(hotkey.replace('0x', ''))
        if len(hotkey_bytes) != 32:
            raise ValueError("Hotkey must be 32 bytes (64 hex characters)")
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
    """Remove stake."""
    contract = get_contract(w3, contract_address)
    
    # Convert hotkey string to bytes32
    if isinstance(hotkey, str):
        hotkey_bytes = bytes.fromhex(hotkey.replace('0x', ''))
        if len(hotkey_bytes) != 32:
            raise ValueError("Hotkey must be 32 bytes (64 hex characters)")
        hotkey = hotkey_bytes
    
    # Build transaction
    tx = contract.functions.removeStake(
        hotkey,
        netuid,
        amount
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
                raise ValueError(f"Amount ({amount} wei) exceeds contract balance ({balance} wei)")
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
        raise ValueError(f"Amount ({amount} wei) exceeds contract balance ({balance} wei)")
    
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


def main():
    parser = argparse.ArgumentParser(description='Interact with StakeWrap contract')
    parser.add_argument('action', choices=['stake', 'stakeLimit', 'removeStake', 'owner', 'withdraw', 'withdrawTo', 'balance'],
                       help='Action to perform')
    parser.add_argument('--hotkey', type=str, help='Hotkey (32 bytes hex string)')
    parser.add_argument('--netuid', type=int, help='Network UID')
    parser.add_argument('--amount', type=int, help='Amount to stake/unstake/withdraw (in wei)')
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
        stake(w3, account, contract_address, args.hotkey, args.netuid, args.amount)
    
    elif args.action == 'stakeLimit':
        if not all([args.hotkey, args.netuid is not None, args.limit_price is not None,
                   args.amount is not None]):
            parser.error("stakeLimit requires --hotkey, --netuid, --limit-price, and --amount")
        stake_limit(w3, account, contract_address, args.hotkey, args.netuid,
                   args.limit_price, args.amount, args.allow_partial)
    
    elif args.action == 'removeStake':
        if not all([args.hotkey, args.netuid is not None, args.amount is not None]):
            parser.error("removeStake requires --hotkey, --netuid, and --amount")
        remove_stake(w3, account, contract_address, args.hotkey, args.netuid, args.amount)
    
    elif args.action == 'withdraw':
        withdraw(w3, account, contract_address, args.amount)
    
    elif args.action == 'withdrawTo':
        if not all([args.to, args.amount is not None]):
            parser.error("withdrawTo requires --to and --amount")
        withdraw_to(w3, account, contract_address, args.to, args.amount)


if __name__ == '__main__':
    main()

