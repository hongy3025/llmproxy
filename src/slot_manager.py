"""
槽位管理模块。

负责与 llama-server 的槽位（Slot）机制交互，实现会话上下文的持久化、前缀匹配及槽位状态克隆。
"""

import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel

from llama_client import LlamaServerClient


class Slot(BaseModel):
    """
    表示 llama-server 中的一个槽位状态模型。
    """

    id: int
    """槽位唯一标识符。"""

    session_id: Optional[str] = None
    """当前绑定到该槽位的会话 ID。"""

    last_accessed: float = 0.0
    """最后访问的时间戳（用于 LRU 淘汰）。"""

    state: int = 0  # 0: idle, 1: processing
    """槽位当前状态：0 为空闲，1 为处理中。"""


class SessionSlotMapping(BaseModel):
    """
    会话与槽位的映射记录模型。
    """

    session_id: str
    """会话的唯一标识符。"""

    slot_id: int
    """绑定的槽位 ID。"""


class SlotManager:
    """
    全局槽位管理器类。

    管理内存中的槽位状态、Token 缓存，处理新会话请求时的最佳匹配和槽位分配。
    """

    _slots: Dict[int, Slot] = {}
    """内存中槽位 ID 到槽位对象的映射表。"""

    _session_to_slot: Dict[str, int] = {}
    """会话 ID 到当前绑定槽位 ID 的映射表。"""

    _slot_token_cache: Dict[int, List[int]] = {}
    """槽位 ID 到其对应 Token 序列的缓存，用于前缀匹配优化。"""

    _lock: asyncio.Lock = asyncio.Lock()
    """并发访问锁，确保槽位分配和状态更新的原子性。"""

    _llama_client: LlamaServerClient
    """与 llama-server 进行 API 交互的客户端。"""

    _slot_save_dir: str = "data/slots"
    """槽位状态持久化数据的存储目录。"""

    def __init__(self, llama_client: LlamaServerClient):
        """
        初始化 SlotManager 实例。

        Args:
            llama_client (LlamaServerClient): 用于与 llama-server 交互的客户端。
        """
        self._llama_client = llama_client
        os.makedirs(self._slot_save_dir, exist_ok=True)

    async def initialize_slots(self):
        """
        从 llama-server 查询并初始化本地槽位跟踪状态。
        """
        async with self._lock:
            try:
                server_slots = await self._llama_client.get_slots()
                for slot_data in server_slots:
                    slot_id = slot_data.get("id")
                    if slot_id is not None:
                        self._slots[slot_id] = Slot(
                            id=slot_id, state=slot_data.get("state", 0)
                        )
                        # 初始化 Token 缓存
                        prompt = slot_data.get("prompt", "")
                        generated = slot_data.get("generated", "")
                        combined_text = prompt + generated
                        if combined_text:
                            tokens = await self._llama_client.tokenize(combined_text)
                            self._slot_token_cache[slot_id] = tokens
                            logger.debug(
                                f"Initialized token cache for slot {slot_id} with {len(tokens)} tokens."
                            )
                logger.info(f"Initialized {len(self._slots)} slots from llama-server.")
            except Exception as e:
                logger.error(f"Failed to initialize slots: {e}")

    def _find_longest_prefix_match(
        self, chat_token_array: List[int]
    ) -> Tuple[Optional[int], int]:
        """
        为给定的 token 数组找到具有最长前缀匹配的槽位。

        Args:
            chat_token_array (List[int]): 待匹配的请求 token 数组。

        Returns:
            Tuple[Optional[int], int]: 匹配到的最佳槽位 ID 及其匹配长度。
        """
        best_slot = None
        max_match_len = 0

        for slot_id, cached_tokens in self._slot_token_cache.items():
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

    def set_slot_state(self, slot_id: int, state: int):
        """
        设置指定槽位的处理状态。

        Args:
            slot_id (int): 槽位 ID。
            state (int): 状态值 (0: idle, 1: processing)。
        """
        if slot_id in self._slots:
            self._slots[slot_id].state = state

    def _get_lru_slot(self) -> int:
        """
        寻找最近最少使用的空闲槽位。

        Returns:
            int: 选定的槽位 ID。
        """
        # Ideally, we find an idle slot (not processing)
        idle_slots = [s for s in self._slots.values() if s.state == 0]
        if not idle_slots:
            # If all are "processing", we fallback to the oldest last_accessed
            # Though we shouldn't steal a processing slot, but as a fallback:
            logger.warning(
                "All slots are currently processing! Forcing eviction of the oldest slot."
            )
            candidate_slots = list(self._slots.values())
        else:
            candidate_slots = idle_slots

        candidate_slots.sort(key=lambda x: x.last_accessed)
        return candidate_slots[0].id

    async def allocate_and_prepare_slot(
        self, session_id: str, chat_token_array: List[int]
    ) -> int:
        """
        为指定会话分配槽位，并根据需要准备槽位状态（如克隆现有槽位）。

        Args:
            session_id (str): 会话标识符。
            chat_token_array (List[int]): 会话对应的最新 token 数组。

        Returns:
            int: 分配到的槽位 ID。
        """
        async with self._lock:
            # Handle empty session_id (anonymous request)
            if not session_id:
                unbound_idle_slots = [
                    s
                    for s in self._slots.values()
                    if s.state == 0 and s.session_id is None
                ]
                if unbound_idle_slots:
                    unbound_idle_slots.sort(key=lambda x: x.last_accessed)
                    target_slot_id = unbound_idle_slots[0].id
                else:
                    target_slot_id = self._get_lru_slot()
                    target_slot = self._slots[target_slot_id]
                    if target_slot.session_id is not None:
                        logger.warning(
                            f"No unbound idle slots available. Evicting session '{target_slot.session_id}' "
                            f"from slot {target_slot_id} for anonymous request."
                        )
                        if target_slot.session_id in self._session_to_slot:
                            del self._session_to_slot[target_slot.session_id]
                        target_slot.session_id = None

                target_slot = self._slots[target_slot_id]
                target_slot.last_accessed = time.time()
                self._slot_token_cache[target_slot_id] = chat_token_array
                return target_slot_id

            # 1. Check if session already has a slot
            if session_id in self._session_to_slot:
                slot_id = self._session_to_slot[session_id]
                if slot_id in self._slots:
                    self._slots[slot_id].last_accessed = time.time()
                    # Update cache
                    self._slot_token_cache[slot_id] = chat_token_array
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
                source_slot = self._slots[source_slot_id]
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

            target_slot = self._slots[target_slot_id]

            # Unbind old session if any
            if (
                target_slot.session_id
                and target_slot.session_id in self._session_to_slot
            ):
                del self._session_to_slot[target_slot.session_id]

            # 4. Clone state if needed
            if needs_clone:
                try:
                    filename = f"slot_{source_slot_id}_to_{target_slot_id}.bin"
                    filepath = os.path.abspath(
                        os.path.join(self._slot_save_dir, filename)
                    )

                    logger.info(
                        f"Cloning slot {source_slot_id} to {target_slot_id} for session {session_id}"
                    )
                    # Save source
                    await self._llama_client.save_slot(source_slot_id, filepath)
                    # Restore to target
                    await self._llama_client.restore_slot(target_slot_id, filepath)

                except Exception as e:
                    logger.error(
                        f"Error cloning slot {source_slot_id} to {target_slot_id}: {e}"
                    )

            # 5. Bind new session to target slot
            target_slot.session_id = session_id
            target_slot.last_accessed = time.time()
            self._session_to_slot[session_id] = target_slot_id
            self._slot_token_cache[target_slot_id] = chat_token_array

            return target_slot_id
