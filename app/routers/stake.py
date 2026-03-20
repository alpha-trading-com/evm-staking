"""Stake and stake-limit endpoints."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth import get_current_username
from app.services import (
    clear_w3_cache,
    get_w3_account_contract,
    is_connection_error,
    receipt_to_dict,
    run_quiet,
    subtensor,
)
from app.schemas import StakeBody, StakeLimitBody
from scripts.interact import stake, stake_limit
from utils.tolerance import calculate_stake_limit_price

router = APIRouter()


@router.post("/api/stake")
async def api_stake(body: StakeBody, _: str = Depends(get_current_username)):
    try:
        w3, account, contract_address, contract = get_w3_account_contract()
        amount_rao = int(body.amount_tao * 10**9)
        receipt = run_quiet(
            stake, w3, account, contract_address, body.hotkey, body.netuid, amount_rao,
            contract=contract,
        )
        return {"ok": True, "receipt": receipt_to_dict(receipt)}
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/api/stake-limit")
async def api_stake_limit(body: StakeLimitBody, _: str = Depends(get_current_username)):
    try:
        w3, account, contract_address, contract = get_w3_account_contract()
        amount_rao = int(body.amount_tao * 10**9)
        limit_price = int(calculate_stake_limit_price(
            tao_amount=body.amount_tao,
            netuid=body.netuid,
            min_tolerance_staking=body.use_min_tolerance,
            default_rate_tolerance=body.rate_tolerance,
            subtensor=subtensor,
        ))
        receipt = run_quiet(
            stake_limit,
            w3, account, contract_address,
            body.hotkey, body.netuid, limit_price, amount_rao,
            body.allow_partial,
            contract=contract,
        )
        return {"ok": True, "receipt": receipt_to_dict(receipt), "limit_price_used": limit_price}
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
