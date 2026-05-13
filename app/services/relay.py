import asyncio
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class RelayManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.setdefault(user_id, set()).add(ws)

    async def disconnect(self, user_id: str, ws: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(user_id, set())
            conns.discard(ws)
            if not conns:
                self._connections.pop(user_id, None)

    async def broadcast(self, message: str) -> None:
        dead: list[tuple[str, WebSocket]] = []
        for user_id, conns in list(self._connections.items()):
            for ws in list(conns):
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append((user_id, ws))
        for uid, ws in dead:
            await self.disconnect(uid, ws)

    async def send_to_user(self, user_id: str, message: str) -> None:
        conns = list(self._connections.get(user_id, set()))
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)


relay_manager = RelayManager()
