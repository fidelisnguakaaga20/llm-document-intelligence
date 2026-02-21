import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.auth.jwt_handler import verify_token
from app.streaming.broadcaster import broadcaster

router = APIRouter(prefix="/documents", tags=["Streaming"])


@router.get("/stream")
async def stream_documents(
    request: Request,
    user: dict = Depends(verify_token),
):
    q = broadcaster.subscribe()

    async def event_generator():
        try:
            while True:
                # client disconnected
                if await request.is_disconnected():
                    break

                event = await q.get()
                data = json.dumps(event)

                yield f"event: status\n"
                yield f"data: {data}\n\n"
        finally:
            broadcaster.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")