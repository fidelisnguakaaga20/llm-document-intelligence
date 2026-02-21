from collections import deque
from threading import Lock
from typing import Optional, Deque, Set, List


class FIFOQueue:
    """
    In-memory FIFO queue with:
    - strict order (deque)
    - no duplicates (set)
    - thread-safe operations (Lock)
    """

    def __init__(self) -> None:
        self._q: Deque[str] = deque()
        self._seen: Set[str] = set()
        self._lock = Lock()

    def enqueue(self, document_id: str) -> bool:
        """Returns True if added, False if already queued."""
        with self._lock:
            if document_id in self._seen:
                return False
            self._q.append(document_id)
            self._seen.add(document_id)
            return True

    def dequeue(self) -> Optional[str]:
        """Returns next document_id or None if empty."""
        with self._lock:
            if not self._q:
                return None
            doc_id = self._q.popleft()
            self._seen.discard(doc_id)
            return doc_id

    def snapshot(self) -> List[str]:
        """For debugging/verification."""
        with self._lock:
            return list(self._q)

    def size(self) -> int:
        with self._lock:
            return len(self._q)


# Global singleton queue instance used by routes/workers
document_queue = FIFOQueue()