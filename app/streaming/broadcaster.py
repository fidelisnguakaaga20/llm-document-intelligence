import asyncio
from typing import Dict, Any, Set


class Broadcaster:
    def __init__(self) -> None:
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    async def publish(self, event: Dict[str, Any]) -> None:
        # Fan-out to all subscribers (best-effort)
        dead = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(event)
            except Exception:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)


broadcaster = Broadcaster()