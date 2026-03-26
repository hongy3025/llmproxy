"""
简单的非交互式聊天客户端脚本。

用于向 llmproxy 服务发送单次聊天请求并打印响应。
支持流式和非流式输出。
"""

import argparse
import json
import sys
import uuid

import httpx


def main():
    parser = argparse.ArgumentParser(description="llmproxy 简单聊天客户端")
    parser.add_argument("message", type=str, help="要发送的消息内容")
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8080/v1/chat/completions",
        help="服务地址",
    )
    parser.add_argument("--stream", action="store_true", help="是否启用流式响应")
    parser.add_argument("--session-id", type=str, help="会话 ID (若未指定则自动生成)")
    parser.add_argument("--model", type=str, default="llama", help="模型名称")
    parser.add_argument("--system", type=str, help="可选的 system prompt 内容")
    parser.add_argument("--verbose", action="store_true", help="显示详细调试信息")

    args = parser.parse_args()

    session_id = args.session_id or str(uuid.uuid4())

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.message})

    if args.verbose:
        print(f"Connecting to: {args.url}")
        print(f"Session ID: {session_id}")
        print(
            f"Payload: {json.dumps({'model': args.model, 'messages': messages, 'stream': args.stream}, ensure_ascii=False)}"
        )

    headers = {
        "Content-Type": "application/json",
        "X-Session-ID": session_id,
        "User-Agent": "SimpleChatClient/1.0",
    }

    payload = {
        "model": args.model,
        "messages": messages,
        "stream": args.stream,
    }

    try:
        if args.stream:
            with httpx.stream(
                "POST", args.url, json=payload, headers=headers, timeout=60.0
            ) as response:
                if response.status_code != 200:
                    print(f"Error: {response.status_code}")
                    print(response.read().decode())
                    return

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            content = data["choices"][0]["delta"].get("content", "")
                            print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            continue
                print()  # 换行
        else:
            response = httpx.post(args.url, json=payload, headers=headers, timeout=60.0)
            if args.verbose:
                print(f"Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        print(content)
                    else:
                        print(
                            f"Warning: 'message' or 'content' not found in response choice: {choice}"
                        )
                else:
                    print(f"Warning: 'choices' not found or empty in response: {data}")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)

    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
        print(str(exc))
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
