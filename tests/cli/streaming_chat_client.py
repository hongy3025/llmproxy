import json
import os
import sys

import httpx


def main():
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("Error: LLM_API_KEY environment variable not set.")
        sys.exit(1)

    url = "http://localhost:8080/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "X-Session-ID": "test-session-streaming-cli",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "你是一个快捷助手，专注于提供简洁、精准的回答。无需冗长解释或多步推理，直接给出最核心的信息或答案。保持高效，避免多余内容。",
            },
            {
                "role": "user",
                "content": "广州有哪些好玩的地方？",
            },
        ],
        "stream": True,
    }

    print(f"Sending streaming request to {url}...")
    try:
        with httpx.Client(timeout=60.0) as client:
            with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()

                print("\nResponse Status Code:", response.status_code)
                print("Response Headers:", dict(response.headers))
                print("\nResponse Body (Streaming):")

                for line in response.iter_lines():
                    if not line:
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            print("\n[Stream Finished]")
                            break

                        try:
                            data_json = json.loads(data_str)
                            # Most streaming formats for OpenAI have content in choices[0].delta.content
                            choices = data_json.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            print(f"\nCould not parse line: {line}")

    except httpx.HTTPError as e:
        print(f"\nHTTP Error occurred: {e}")
        if hasattr(e, "response") and e.response:
            print("Response text:", e.response.text)
    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()
