"""Contract/account status endpoint."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from web3 import Web3

from app.auth import get_current_username
from app.services import (
    clear_w3_cache,
    get_w3_account_contract,
    is_connection_error,
)

router = APIRouter()


@router.get("/api/status")
async def api_status(_: str = Depends(get_current_username)):
    try:
        w3, account, contract_address, contract = get_w3_account_contract()
        balance_wei = w3.eth.get_balance(contract_address)
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    balance_tao = float(Web3.from_wei(balance_wei, "ether"))
    try:
        owner = contract.functions.owner().call()
    except Exception:
        owner = None
    return {
        "ok": True,
        "contract": contract_address,
        "account": account.address,
        "owner": owner,
        "is_owner": bool(owner and owner.lower() == account.address.lower()),
        "balance_wei": str(balance_wei),
        "balance_tao": balance_tao,
        "chain_id": w3.eth.chain_id,
    }