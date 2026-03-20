"""Request body schemas for API endpoints."""
from pydantic import BaseModel


class StakeBody(BaseModel):
    hotkey: str
    netuid: int
    amount_tao: float


class StakeLimitBody(BaseModel):
    hotkey: str
    netuid: int
    amount_tao: float
    rate_tolerance: float = 0.5
    use_min_tolerance: bool = False
    allow_partial: bool = False


class RemoveStakeBody(BaseModel):
    hotkey: str
    netuid: int
    amount: float | None = None


class RemoveStakeLimitBody(BaseModel):
    hotkey: str
    netuid: int
    amount: float | None = None
    rate_tolerance: float = 0.5
    use_min_tolerance: bool = False
    allow_partial: bool = False


class TransferStakeBody(BaseModel):
    hotkey: str
    origin_netuid: int
    destination_netuid: int
    amount_tao: float


class MoveStakeBody(BaseModel):
    origin_hotkey: str
    destination_hotkey: str
    origin_netuid: int
    destination_netuid: int
    amount_tao: float | None = None


class WithdrawBody(BaseModel):
    amount_tao: float


class CalcToleranceBody(BaseModel):
    tao_amount: float
    netuid: int
    operation: str = "stake"  # "stake" or "unstake"
