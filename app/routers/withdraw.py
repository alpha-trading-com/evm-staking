"""Withdraw endpoint."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth import get_current_username
from app.services import (
    clear_w3_cache,
    get_w3_account_contract,
    is_connection_error,
    receipt_to_dict,
    run_quiet,
)
from app.schemas import WithdrawBody
from scripts.interact import withdraw

router = APIRouter()


@router.post("/api/withdraw")
async def api_withdraw(body: WithdrawBody, _: str = Depends(get_current_username)):
    try:
        w3, account, contract_address, contract = get_w3_account_contract()
        amount_wei = int(body.amount_tao * 10**18)
        receipt = run_quiet(withdraw, w3, account, contract_address, amount_wei, contract=contract)
        return {"ok": True, "receipt": receipt_to_dict(receipt)}
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
