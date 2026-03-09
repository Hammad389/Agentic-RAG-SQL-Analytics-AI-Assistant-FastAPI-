import threading

from app.infrastructure.ai.openai_client import OpenAIClientProvider


def warm_openai():
    try:
        client = OpenAIClientProvider.get_client()
        client.responses.create(
            model="gpt-4o-mini",
            input="ping",
            max_output_tokens=16,
        )
        print("[WARMUP] OpenAI warmup completed.")
    except Exception as e:
        print("[WARMUP] OpenAI warmup failed:", e)


def start_warmup_background():
    thread = threading.Thread(target=warm_openai, daemon=True)
    thread.start()
