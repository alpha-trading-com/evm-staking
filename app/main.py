"""
FastAPI app for StakeWrap: stake, stake limit, unstake, unstake limit, transfer stake, move stake, withdraw.

Same-block note: if sending unstake and stake in one block, send unstake first, then stake
(stake then unstake in same block fails because the precompile does not see the new stake yet).

Run from repo root:
  uvicorn app.main:app --host 0.0.0.0 --port 8000

Or: ./run_server.sh
"""
import app.config  # noqa: F401 - path and env setup

from fastapi import FastAPI

from app.routers import (
    pages_router,
    status_router,
    stake_router,
    unstake_router,
    transfer_router,
    withdraw_router,
    tools_router,
)

app = FastAPI(title="StakeWrap Control", version="1.0.0")

app.include_router(pages_router)
app.include_router(status_router)
app.include_router(stake_router)
app.include_router(unstake_router)
app.include_router(transfer_router)
app.include_router(withdraw_router)
app.include_router(tools_router)
