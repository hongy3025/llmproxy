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
        "X-Session-ID": "test-session-cli",
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"},
        ],
        "stream": False,
    }

    print(f"Sending request to {url}...")
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            print("\nResponse Status Code:", response.status_code)
            print("Response Headers:", dict(response.headers))

            try:
                result = response.json()
                print("\nResponse Body (JSON):")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print("\nResponse Body (Text):")
                print(response.text)

    except httpx.HTTPError as e:
        print(f"\nHTTP Error occurred: {e}")
        if hasattr(e, "response") and e.response:
            print("Response text:", e.response.text)
    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    main()
