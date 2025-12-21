import os
import sys

def main() -> int:
    key = os.getenv("GROQ_API_KEY")
    rpc = os.getenv("RPC_URL")
    plex = os.getenv("PERPLEXITY_API_KEY")

    print("GROQ_KEY_PRESENT", bool(key))
    print("GROQ_KEY_LEN", len(key) if key else 0)
    print("RPC_URL_PRESENT", bool(rpc))
    print("RPC_URL", (rpc[:80] + "...") if rpc else None)
    print("PERPLEXITY_KEY_PRESENT", bool(plex))

    try:
        import httpx
    except Exception as e:
        print("httpx import failed:", e)
        return 1

    errors: list[str] = []

    if key:
        try:
            r = httpx.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10,
            )
            print("GROQ_STATUS", r.status_code)
            if r.status_code == 200:
                data = r.json()
                names = [m.get("id") for m in data.get("data", [])][:5]
                print("GROQ_MODELS_SAMPLE", names)
            else:
                errors.append(f"groq status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            errors.append(f"groq check error: {e}")
    else:
        errors.append("missing GROQ_API_KEY")

    if rpc:
        try:
            payload = {"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1}
            r = httpx.post(rpc, json=payload, timeout=10)
            print("RPC_STATUS", r.status_code)
            print("RPC_BODY", r.text[:200])
            if r.status_code != 200:
                errors.append(f"rpc status {r.status_code}")
        except Exception as e:
            errors.append(f"rpc check error: {e}")
    else:
        errors.append("missing RPC_URL")

    if plex is None:
        errors.append("missing PERPLEXITY_API_KEY")

    if errors:
        print("ERRORS", errors)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
