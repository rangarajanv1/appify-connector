from fastapi import APIRouter, Request, Response, status

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@router.get("/livez")
async def livez() -> dict:
    return {"status": "alive"}


@router.get("/readyz")
async def readyz(request: Request, response: Response) -> dict:
    store = request.app.state.session_store
    try:
        await store.ping()
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not-ready", "reason": "redis-unreachable"}
    return {"status": "ready"}
