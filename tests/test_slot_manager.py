from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from llama_client import LlamaServerClient
from slot_manager import SlotManager


@pytest.fixture
def mock_llama_client():
    client = MagicMock(spec=LlamaServerClient)
    client.get_slots = AsyncMock(
        return_value=[
            {"id": 0, "state": 0},
            {"id": 1, "state": 0},
            {"id": 2, "state": 0},
        ]
    )
    client.save_slot = AsyncMock(return_value=True)
    client.restore_slot = AsyncMock(return_value=True)
    return client


@pytest_asyncio.fixture
async def slot_manager(mock_llama_client):
    manager = SlotManager(mock_llama_client)
    await manager.initialize_slots()
    return manager


@pytest.mark.asyncio
async def test_prefix_matching(slot_manager):
    # Setup cache
    slot_manager.slot_token_cache = {
        0: [1, 2, 3, 4, 5],
        1: [1, 2, 3, 6, 7],
        2: [1, 2, 8, 9, 10],
    }

    # Test longest prefix match
    best_slot, match_len = slot_manager._find_longest_prefix_match([1, 2, 3, 4, 11])
    assert best_slot == 0
    assert match_len == 4

    # Test another match
    best_slot, match_len = slot_manager._find_longest_prefix_match([1, 2, 3, 6, 12])
    assert best_slot == 1
    assert match_len == 4

    # Test short match (matches 0, 1, and 2 equally, returns first found)
    best_slot, match_len = slot_manager._find_longest_prefix_match([1, 2, 10, 11])
    assert match_len == 2

    # Test no match
    best_slot, match_len = slot_manager._find_longest_prefix_match([99, 100])
    # With 0 match length, it technically returns the first one it checked with match_len=0,
    # but we only care about it if match_len > 10 usually, let's just check length
    assert match_len == 0


@pytest.mark.asyncio
async def test_lru_slot_allocation(slot_manager):
    # Setup slots with different last_accessed times
    slot_manager.slots[0].last_accessed = 100.0
    slot_manager.slots[0].state = 0

    slot_manager.slots[1].last_accessed = 50.0  # LRU
    slot_manager.slots[1].state = 0

    slot_manager.slots[2].last_accessed = 150.0
    slot_manager.slots[2].state = 0

    lru_slot = slot_manager._get_lru_slot()
    assert lru_slot == 1

    # Make slot 1 processing
    slot_manager.slots[1].state = 1
    lru_slot = slot_manager._get_lru_slot()
    # Now slot 0 is LRU among idle slots
    assert lru_slot == 0


@pytest.mark.asyncio
async def test_allocate_and_prepare_slot_reuse(slot_manager):
    # Session already has a slot
    slot_manager.session_to_slot["session_A"] = 1
    slot_manager.slots[1].session_id = "session_A"

    slot_id = await slot_manager.allocate_and_prepare_slot("session_A", [1, 2, 3])

    assert slot_id == 1
    assert slot_manager.slot_token_cache[1] == [1, 2, 3]


@pytest.mark.asyncio
async def test_allocate_and_prepare_slot_clone(slot_manager):
    # Setup token cache to force a clone (> 10 tokens match)
    source_tokens = [i for i in range(20)]
    slot_manager.slot_token_cache[0] = source_tokens
    slot_manager.slots[0].session_id = "session_A"

    # Target tokens
    target_tokens = source_tokens[:15] + [99, 100]

    # Make slot 1 the LRU
    slot_manager.slots[1].last_accessed = 10.0
    slot_manager.slots[0].last_accessed = 100.0
    slot_manager.slots[2].last_accessed = 200.0

    slot_id = await slot_manager.allocate_and_prepare_slot("session_B", target_tokens)

    # Should allocate slot 1
    assert slot_id == 1

    # Should have cloned from 0 to 1
    slot_manager.llama_client.save_slot.assert_called_once()
    slot_manager.llama_client.restore_slot.assert_called_once()

    assert slot_manager.session_to_slot["session_B"] == 1
    assert slot_manager.slots[1].session_id == "session_B"
    assert slot_manager.slot_token_cache[1] == target_tokens
