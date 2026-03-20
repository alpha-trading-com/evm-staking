"""Transfer-stake and move-stake endpoints."""
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
from app.schemas import TransferStakeBody, MoveStakeBody
from scripts.interact import transfer_stake, move_stake

router = APIRouter()


@router.post("/api/transfer-stake")
async def api_transfer_stake(body: TransferStakeBody, _: str = Depends(get_current_username)):
    try:
        w3, account, contract_address, contract = get_w3_account_contract()
        amount_rao = int(body.amount_tao * 10**9)
        receipt = run_quiet(
            transfer_stake,
            w3, account, contract_address,
            body.hotkey, body.origin_netuid, body.destination_netuid, amount_rao,
            contract=contract,
        )
        return {"ok": True, "receipt": receipt_to_dict(receipt)}
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/api/move-stake")
async def api_move_stake(body: MoveStakeBody, _: str = Depends(get_current_username)):
    try:
        w3, account, contract_address, contract = get_w3_account_contract()
        if body.amount_tao is None:
            stake_balance = subtensor.get_stake(
                coldkey_ss58=COLDKEY_SS58,
                hotkey_ss58=body.origin_hotkey,
                netuid=body.origin_netuid,
            )
            amount_rao = stake_balance.rao - 1
        elif 0 < body.amount_tao < 1:
            stake_balance = subtensor.get_stake(
                coldkey_ss58=COLDKEY_SS58,
                hotkey_ss58=body.origin_hotkey,
                netuid=body.origin_netuid,
            )
            amount_rao = int(body.amount_tao * stake_balance.rao)
        else:
            amount_rao = int(body.amount_tao * 10**9)
        receipt = run_quiet(
            move_stake,
            w3, account, contract_address,
            body.origin_hotkey, body.destination_hotkey,
            body.origin_netuid, body.destination_netuid,
            amount_rao,
            contract=contract,
        )
        return {"ok": True, "receipt": receipt_to_dict(receipt)}
    except Exception as e:
        if is_connection_error(e):
            clear_w3_cache()
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
