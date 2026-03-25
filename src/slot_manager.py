import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel

from llama_client import LlamaServerClient


class Slot(BaseModel):
    id: int
    session_id: Optional[str] = None
    last_accessed: float = 0.0
    prompt: str = ""
    state: int = 0  # 0: idle, 1: processing


class SessionSlotMapping(BaseModel):
    session_id: str
    slot_id: int


class SlotManager:
    def __init__(self, llama_client: LlamaServerClient):
        self.slots: Dict[int, Slot] = {}
        self.session_to_slot: Dict[str, int] = {}
        self.slot_token_cache: Dict[int, List[int]] = {}
        self.lock = asyncio.Lock()
        self.llama_client = llama_client
        self.slot_save_dir = "data/slots"
        os.makedirs(self.slot_save_dir, exist_ok=True)

    async def initialize_slots(self):
        """Initialize slot tracking by querying the server."""
        async with self.lock:
            try:
                server_slots = await self.llama_client.get_slots()
                for slot_data in server_slots:
                    slot_id = slot_data.get("id")
                    if slot_id is not None:
                        self.slots[slot_id] = Slot(
                            id=slot_id, state=slot_data.get("state", 0)
                        )
                        # We might not know the session_id or token cache yet.
                logger.info(f"Initialized {len(self.slots)} slots from llama-server.")
            except Exception as e:
                logger.error(f"Failed to initialize slots: {e}")

    def _find_longest_prefix_match(
        self, chat_token_array: List[int]
    ) -> Tuple[Optional[int], int]:
        """Find the slot with the longest prefix match for the given token array."""
        best_slot = None
        max_match_len = 0

        for slot_id, cached_tokens in self.slot_token_cache.items():
            match_len = 0
            for c_tok, t_tok in zip(cached_tokens, chat_token_array):
                if c_tok == t_tok:
                    match_len += 1
                else:
                    break

            if match_len > max_match_len:
                max_match_len = match_len
                best_slot = slot_id

        return best_slot, max_match_len

    def _get_lru_slot(self) -> int:
        """Find the least recently used slot that is currently idle."""
        # Ideally, we find an idle slot (not processing)
        idle_slots = [s for s in self.slots.values() if s.state == 0]
        if not idle_slots:
            # If all are "processing", we fallback to the oldest last_accessed
            # Though we shouldn't steal a processing slot, but as a fallback:
            candidate_slots = list(self.slots.values())
        else:
            candidate_slots = idle_slots

        candidate_slots.sort(key=lambda x: x.last_accessed)
        return candidate_slots[0].id

    async def allocate_and_prepare_slot(
        self, session_id: str, chat_token_array: List[int]
    ) -> int:
        """Allocate a slot for the session and prepare it (clone if needed)."""
        async with self.lock:
            # 1. Check if session already has a slot
            if session_id in self.session_to_slot:
                slot_id = self.session_to_slot[session_id]
                if slot_id in self.slots:
                    self.slots[slot_id].last_accessed = time.time()
                    # Update cache
                    self.slot_token_cache[slot_id] = chat_token_array
                    logger.debug(f"Session {session_id} reused existing slot {slot_id}")
                    return slot_id

            # 2. Find longest prefix match
            source_slot_id, match_len = self._find_longest_prefix_match(
                chat_token_array
            )
            logger.debug(
                f"Session {session_id} best prefix match is slot {source_slot_id} (len: {match_len})"
            )

            target_slot_id = None
            needs_clone = False

            # 3. Decide target slot and whether to clone
            if source_slot_id is not None and match_len > 10:
                source_slot = self.slots[source_slot_id]
                # If the best matched slot is not bound to any session, use it directly
                if source_slot.session_id is None:
                    target_slot_id = source_slot_id
                else:
                    # Allocate a new LRU slot and clone
                    target_slot_id = self._get_lru_slot()
                    if target_slot_id != source_slot_id:
                        needs_clone = True
            else:
                # No good match, just get an LRU slot
                target_slot_id = self._get_lru_slot()

            target_slot = self.slots[target_slot_id]

            # Unbind old session if any
            if (
                target_slot.session_id
                and target_slot.session_id in self.session_to_slot
            ):
                del self.session_to_slot[target_slot.session_id]

            # 4. Clone state if needed
            if needs_clone:
                try:
                    filename = f"slot_{source_slot_id}_to_{target_slot_id}.bin"
                    filepath = os.path.abspath(
                        os.path.join(self.slot_save_dir, filename)
                    )

                    logger.info(
                        f"Cloning slot {source_slot_id} to {target_slot_id} for session {session_id}"
                    )
                    # Save source
                    await self.llama_client.save_slot(source_slot_id, filepath)
                    # Restore to target
                    await self.llama_client.restore_slot(target_slot_id, filepath)

                except Exception as e:
                    logger.error(
                        f"Error cloning slot {source_slot_id} to {target_slot_id}: {e}"
                    )

            # 5. Bind new session to target slot
            target_slot.session_id = session_id
            target_slot.last_accessed = time.time()
            self.session_to_slot[session_id] = target_slot_id
            self.slot_token_cache[target_slot_id] = chat_token_array

            return target_slot_id
