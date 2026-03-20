"""Remove-stake and remove-stake-limit endpoints."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth import get_current_username
from app.config import COLDKEY_SS58
from app.services import (
    clear_w3_cache,
    get_w3_account_contract,
    is_connection_error,
    receipt_to_dict,
    run_quiet,
    subtensor,
)
from app.schemas import RemoveStakeBody, RemoveStakeLimitBody
from scripts.interact import remove_stake, remove_stake_limit
from utils.tolerance import calculate_unstake_limit_price

router = APIRouter()


@router.post("/api/remove-stake")
async def api_remove_stake(body: RemoveStakeBody, _: str = Depends(get_current_username)):
    try:
        w3, account, contract_address = get_w3_account_contract()
        if body.amount is None:
            stake_balance = subtensor.get_stake(
                coldkey_ss58=COLDKEY_SS58,
                hotkey_ss58=body.hotkey,
                netuid=body.netuid,
            )
            amount_alpha_rao = max(0, stake_balance.rao - 1)
            if amount_alpha_rao == 0:
                return JSONResponse(
                    {"ok": False, "error": "Nothing to unstake (balance is zero or too small)"},
                    status_code=400,
                )
        elif 0 < body.amount < 1:
            stake_balance = subtensor.get_stake(
                coldkey_ss58=COLDKEY_SS58,
                hotkey_ss58=body.hotkey,
                netuid=body.netuid,
            )
            amount_alpha_rao = int(body.amount * stake_balance.rao)
        else:
            amount_alpha_rao = int(body.amount * 10**9)
        if amount_alpha_rao < 0:
            return JSONResponse(
                {"ok": False, "error": "Unstake amount would be negative (e.g. zero balance or race with another tx)"},
                status_code=400,
            )
        receipt = run_quiet(
            remove_stake, w3, account, contract_address,
            body.hotkey, body.netuid, amount_alpha_rao,
        )
        return {"ok": True, "receipt": receipt_to_dict(receipt)}
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/api/remove-stake-limit")
async def api_remove_stake_limit(body: RemoveStakeLimitBody, _: str = Depends(get_current_username)):
    try:
        w3, account, contract_address = get_w3_account_contract()
        if body.amount is None:
            stake_balance = subtensor.get_stake(
                coldkey_ss58=COLDKEY_SS58,
                hotkey_ss58=body.hotkey,
                netuid=body.netuid,
            )
            amount_alpha_rao = max(0, stake_balance.rao - 1)
            if amount_alpha_rao == 0:
                return JSONResponse(
                    {"ok": False, "error": "Nothing to unstake (balance is zero or too small)"},
                    status_code=400,
                )
            amount_tao = stake_balance.tao
        elif 0 < body.amount < 1:
            stake_balance = subtensor.get_stake(
                coldkey_ss58=COLDKEY_SS58,
                hotkey_ss58=body.hotkey,
                netuid=body.netuid,
            )
            amount_alpha_rao = int(body.amount * stake_balance.rao)
            amount_tao = body.amount * stake_balance.tao
        else:
            amount_alpha_rao = int(body.amount * 10**9)
            amount_tao = body.amount / 10**9
        if amount_alpha_rao < 0:
            return JSONResponse(
                {"ok": False, "error": "Unstake amount would be negative (e.g. zero balance or race with another tx)"},
                status_code=400,
            )
        limit_price = int(calculate_unstake_limit_price(
            tao_amount=amount_tao,
            netuid=body.netuid,
            min_tolerance_unstaking=body.use_min_tolerance,
            default_rate_tolerance=body.rate_tolerance,
            subtensor=subtensor,
        ))
        receipt = run_quiet(
            remove_stake_limit,
            w3, account, contract_address,
            body.hotkey, body.netuid, limit_price, amount_alpha_rao,
            body.allow_partial,
        )
        return {"ok": True, "receipt": receipt_to_dict(receipt), "limit_price_used": limit_price}
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
