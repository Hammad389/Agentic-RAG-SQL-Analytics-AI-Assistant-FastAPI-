import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIClientProvider:
    """
    Singleton OpenAI client provider.
    Ensures only one client instance is created.
    """

    _client: OpenAI | None = None

    @classmethod
    def get_client(cls) -> OpenAI:
        if cls._client is None:
            cls._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return cls._client
