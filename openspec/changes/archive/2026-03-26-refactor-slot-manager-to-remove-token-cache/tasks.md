## 1. 移除 `_slot_token_cache`

- [x] 1.1 从 `SlotManager` 类定义中删除 `_slot_token_cache` 字段。
- [x] 1.2 在 `initialize_slots` 方法中移除对 `_slot_token_cache` 的初始化和更新操作。

## 2. 修改前缀匹配逻辑

- [x] 2.1 修改 `_find_longest_prefix_match` 方法，使其能够接收 `server_slots` 作为输入并实时进行 Tokenize 和匹配。
- [x] 2.2 在 `allocate_and_prepare_slot` 中调用 `_llama_client.get_slots()` 获取最新状态，并将其传递给 `_find_longest_prefix_match`。
- [x] 2.3 移除 `allocate_and_prepare_slot` 中所有更新 `_slot_token_cache` 的代码。

## 3. 验证与清理

- [x] 3.1 确保所有对 `_slot_token_cache` 的引用均已移除。
- [x] 3.2 运行测试以确保槽位分配和克隆逻辑仍然正确工作。
- [x] 3.3 执行 `lint.cmd` 确保代码风格符合规范。
