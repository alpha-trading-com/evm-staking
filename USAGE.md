# interact.py Usage Guide

This guide provides examples for using the `interact.py` script to interact with the StakeWrap contract.

## Prerequisites

1. Make sure you have deployed the contract (run `python scripts/deploy.py`)
2. Set up your `.env` file with `RPC_URL` and `PRIVATE_KEY`
3. Ensure your account has sufficient balance for gas fees

## Basic Commands

### 1. Check Contract Owner

View the owner address of the deployed contract:

```bash
python scripts/interact.py owner
```

**Output:**
```
Contract address: 0x...
Account: 0x...
Contract owner: 0x...
```

### 2. Check Contract Balance

Check how much ETH is stored in the contract:

```bash
python scripts/interact.py balance
```

**Output:**
```
Contract address: 0x...
Account: 0x...
Contract balance: 0.1 ETH (100000000000000000 wei)
```

### 3. Stake Tokens

Stake tokens to a hotkey on a specific network:

```bash
python scripts/interact.py stake \
  --hotkey 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --netuid 1 \
  --amount 1000000000000000000
```

**Parameters:**
- `--hotkey`: Hotkey address as 32-byte hex string (64 hex characters, with or without 0x prefix)
- `--netuid`: Network UID (integer)
- `--amount`: Amount to stake in wei (1 ETH = 1000000000000000000 wei)

**Example with 0.5 TAO:**
```bash
python scripts/interact.py stake \
  --hotkey 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --netuid 1 \
  --amount 500000000000000000
```

### 4. Stake with Limit Price

Stake tokens with a limit price (for limit orders):

```bash
python scripts/interact.py stakeLimit \
  --hotkey 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --netuid 1 \
  --limit-price 1000 \
  --amount 1000000000000000000 \
  --allow-partial
```

**Parameters:**
- `--hotkey`: Hotkey address (32-byte hex string)
- `--netuid`: Network UID
- `--limit-price`: Maximum price to pay (integer)
- `--amount`: Amount to stake in wei
- `--allow-partial`: (Optional) Allow partial fill if full amount can't be staked at limit price

**Example without partial fill:**
```bash
python scripts/interact.py stakeLimit \
  --hotkey 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --netuid 1 \
  --limit-price 1000 \
  --amount 1000000000000000000
```

### 5. Remove Stake

Unstake tokens from a hotkey:

```bash
python scripts/interact.py removeStake \
  --hotkey 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --netuid 1 \
  --amount 500000000000000000
```

**Parameters:**
- `--hotkey`: Hotkey address (32-byte hex string)
- `--netuid`: Network UID
- `--amount`: Amount to unstake in wei

### 6. Withdraw All ETH

Withdraw all ETH from the contract to the owner:

```bash
python scripts/interact.py withdraw
```

**Output:**
```
Contract address: 0x...
Account: 0x...
Contract balance: 0.1 ETH (100000000000000000 wei)
Withdraw transaction hash: 0x...
Transaction confirmed in block: 12345
```

### 7. Withdraw Specific Amount

Withdraw a specific amount of ETH from the contract:

```bash
python scripts/interact.py withdraw --amount 50000000000000000
```

**Parameters:**
- `--amount`: Amount to withdraw in wei (0.05 ETH = 50000000000000000 wei)

**Example withdrawing 0.1 ETH:**
```bash
python scripts/interact.py withdraw --amount 100000000000000000
```

### 8. Withdraw to Specific Address

Withdraw ETH from the contract to a specific address:

```bash
python scripts/interact.py withdrawTo \
  --to 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb \
  --amount 100000000000000000
```

**Parameters:**
- `--to`: Recipient address (must be a valid Ethereum address)
- `--amount`: Amount to withdraw in wei

## Using a Different Contract Address

If you want to interact with a contract that's not in `deployment.json`:

```bash
python scripts/interact.py balance --contract 0xYourContractAddress
```

This works with any command:
```bash
python scripts/interact.py owner --contract 0xYourContractAddress
python scripts/interact.py withdraw --contract 0xYourContractAddress
```

## Common Amount Conversions

For convenience, here are common TAO/ETH amounts in wei:

| Amount | Wei Value |
|--------|-----------|
| 0.001 TAO | 1000000000000000 |
| 0.01 TAO | 10000000000000000 |
| 0.1 TAO | 100000000000000000 |
| 1 TAO | 1000000000000000000 |
| 10 TAO | 10000000000000000000 |

## Complete Workflow Example

Here's a complete workflow example:

```bash
# 1. Check contract owner
python scripts/interact.py owner

# 2. Check contract balance
python scripts/interact.py balance

# 3. Stake 1 TAO to a hotkey on netuid 1
python scripts/interact.py stake \
  --hotkey 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --netuid 1 \
  --amount 1000000000000000000

# 4. Check balance again
python scripts/interact.py balance

# 5. Remove 0.5 TAO stake
python scripts/interact.py removeStake \
  --hotkey 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --netuid 1 \
  --amount 500000000000000000

# 6. Withdraw any remaining ETH from contract
python scripts/interact.py withdraw
```

## Troubleshooting

### Error: "Only owner can call this function"
- Make sure the `PRIVATE_KEY` in your `.env` matches the contract owner
- Check the owner with: `python scripts/interact.py owner`

### Error: "Insufficient balance"
- Check contract balance: `python scripts/interact.py balance`
- Make sure you have enough ETH/TAO to stake

### Error: "Hotkey must be 32 bytes"
- Hotkey must be exactly 64 hex characters (with or without 0x prefix)
- Example: `0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef`

### Error: "deployment.json not found"
- Deploy the contract first: `python scripts/deploy.py`

## Environment Variables

Make sure your `.env` file contains:

```bash
RPC_URL=https://test.finney.opentensor.ai/
PRIVATE_KEY=your_private_key_here
```

**⚠️ WARNING**: Never commit your `.env` file or private keys to version control!

