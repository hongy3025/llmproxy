from unittest.mock import AsyncMock, MagicMock
import pytest
from llama_client import LlamaServerClient
from slot_manager import SlotManager


@pytest.mark.asyncio
async def test_initialize_slots_with_token_cache():
    # Setup mock llama client
    mock_client = MagicMock(spec=LlamaServerClient)
    mock_client.get_slots = AsyncMock(
        return_value=[
            {"id": 0, "state": 0, "prompt": "Hello", "generated": " World"},
            {"id": 1, "state": 1, "prompt": "", "generated": ""},
        ]
    )

    # Mock tokenize behavior
    async def mock_tokenize(content):
        if content == "Hello World":
            return [1, 2, 3]
        return []

    mock_client.tokenize = AsyncMock(side_effect=mock_tokenize)

    # Initialize SlotManager
    manager = SlotManager(mock_client)
    await manager.initialize_slots()

    # Verify slot 0
    assert 0 in manager._slots
    assert manager._slots[0].id == 0
    assert manager._slots[0].state == 0
    assert 0 in manager._slot_token_cache
    assert manager._slot_token_cache[0] == [1, 2, 3]

    # Verify slot 1
    assert 1 in manager._slots
    assert manager._slots[1].id == 1
    assert manager._slots[1].state == 1
    assert 1 not in manager._slot_token_cache

    # Verify tokenize was called for slot 0
    mock_client.tokenize.assert_called_with("Hello World")
