import subprocess
from pathlib import Path


def compare_prompts():
    # 定义目录路径
    base_dir = Path("logs/chats")
    diff_dir = base_dir / "diff"

    # 创建 diff 目录（如果不存在）
    diff_dir.mkdir(parents=True, exist_ok=True)

    # 获取所有的 .txt 文件并按文件名排序（由于文件名包含时间戳，排序即为时序）
    txt_files = sorted(list(base_dir.glob("*.txt")))

    if len(txt_files) < 2:
        print(f"找到 {len(txt_files)} 个 .txt 文件，不足以进行比较。")
        return

    print(
        f"找到 {len(txt_files)} 个 prompt 文件，开始生成 {len(txt_files) - 1} 个 diff 文件..."
    )

    for i in range(len(txt_files) - 1):
        p1 = txt_files[i]
        p2 = txt_files[i + 1]

        # 提取文件名（不带扩展名）用于生成 diff 文件名
        name1 = p1.stem
        name2 = p2.stem
        diff_file = diff_dir / f"diff_{name1}_vs_{name2}.txt"

        # 构建 git diff 命令
        # git diff --no-index --word-diff=plain --word-diff-regex=. p1.txt p2.txt > p1-p2.txt
        cmd = [
            "git",
            "diff",
            "--no-index",
            "--word-diff=plain",
            "--word-diff-regex=.",
            str(p1),
            str(p2),
        ]

        try:
            # 运行命令并捕获输出
            # 注意：git diff --no-index 在发现差异时会返回非零退出码 (1)
            # 使用 check=False，并手动处理可能的编码问题
            result = subprocess.run(cmd, capture_output=True, text=False)

            # 尝试使用 utf-8 解码，如果失败则使用 ignore 或 replace
            try:
                stdout_str = result.stdout.decode("utf-8")
            except UnicodeDecodeError:
                stdout_str = result.stdout.decode("utf-8", errors="replace")

            # 将 diff 结果写入文件
            with open(diff_file, "w", encoding="utf-8") as f:
                f.write(stdout_str)

            print(f"已生成: {diff_file.name}")

        except Exception as e:
            print(f"比较 {p1.name} 和 {p2.name} 时出错: {e}")


if __name__ == "__main__":
    compare_prompts()
