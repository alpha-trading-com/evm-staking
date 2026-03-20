"""Calc-min-tolerance, stake-info, and settings (tolerance_offset) endpoints."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth import get_current_username
from app.config import COLDKEY_SS58
from app.core.config import load_tolerance_offset, update_tolerance_offset
from app.services import subtensor
from app.schemas import CalcToleranceBody, ToleranceOffsetBody
from utils.tolerance import calculate_stake_limit_price, calculate_unstake_limit_price

router = APIRouter()


# --- Tolerance offset settings ---

@router.get("/api/settings/tolerance-offset")
async def get_tolerance_offset(_: str = Depends(get_current_username)):
    """Return current tolerance_offset value (from file)."""
    try:
        value = load_tolerance_offset()
        return {"ok": True, "value": value}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@router.post("/api/settings/tolerance-offset")
async def set_tolerance_offset(body: ToleranceOffsetBody, _: str = Depends(get_current_username)):
    """Set tolerance_offset. Use string e.g. \"*1.1\" for multiplier."""
    try:
        value = body.value
        if isinstance(value, (int, float)):
            value = float(value)
        else:
            value = str(value).strip()
        if not update_tolerance_offset(value):
            return JSONResponse({"ok": False, "error": "Failed to save tolerance_offset"}, status_code=500)
        return {"ok": True, "value": value}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.post("/api/calc-min-tolerance")
async def api_calc_min_tolerance(body: CalcToleranceBody, _: str = Depends(get_current_username)):
    """Calculate minimum tolerance for staking/unstaking operations."""
    try:
        if body.operation == "stake":
            limit_price = int(calculate_stake_limit_price(
                tao_amount=body.tao_amount,
                netuid=body.netuid,
                min_tolerance_staking=True,
                default_rate_tolerance=0.0,
                subtensor=subtensor,
            ))
        else:
            limit_price = int(calculate_unstake_limit_price(
                tao_amount=body.tao_amount,
                netuid=body.netuid,
                min_tolerance_unstaking=True,
                default_rate_tolerance=0.0,
                subtensor=subtensor,
            ))
        return {"ok": True, "limit_price": limit_price, "operation": body.operation}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@router.get("/api/stake-info")
async def api_stake_info(_: str = Depends(get_current_username)):
    """Get stake info for the configured coldkey."""
    try:
        from bittensor import Balance
        from utils.stake_list_v2 import get_amount_with_sim_swap

        stake_infos = subtensor.get_stake_info_for_coldkey(coldkey_ss58=COLDKEY_SS58)
        subnet_infos = subtensor.all_subnets()
        balance = subtensor.get_balance(COLDKEY_SS58)

        stake_list = []
        total_staked_value = 0.0
        for info in stake_infos:
            subnet_info = subnet_infos[info.netuid]
            value = get_amount_with_sim_swap(subtensor, info.stake, info.netuid)
            total_staked_value += value
            stake_list.append({
                "netuid": info.netuid,
                "subnet_name": subnet_info.subnet_name,
                "value_tao": round(value, 2),
                "stake_alpha_tao": round(info.stake.tao, 2),
                "stake_alpha_rao": info.stake.rao,
                "price_tao": round(subnet_info.price.tao, 4),
                "hotkey_ss58": info.hotkey_ss58,
            })

        total_staked_value_balance = Balance.from_tao(total_staked_value)
        total_value = total_staked_value_balance + balance
        return {
            "ok": True,
            "stakes": stake_list,
            "coldkey": COLDKEY_SS58,
            "free_balance_tao": round(balance.tao, 9),
            "total_staked_value_tao": round(total_staked_value_balance.tao, 9),
            "total_value_tao": round(total_value.tao, 9),
        }
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
