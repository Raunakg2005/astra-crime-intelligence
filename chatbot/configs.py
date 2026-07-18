import os
from dataclasses import dataclass

@dataclass
class ChatBotConfig:
    model_name: str = "qwen/qwen3-32b"
    requests_per_minute: int = 60
    max_requests_per_day: int = 1000
    tokens_per_minute: int = 6000
    max_tokens_per_day: int = 500000
    api_base_url: str = f"http://127.0.0.1:{os.environ.get('X_ZOHO_CATALYST_LISTEN_PORT', '8000')}"
    api_timeout_s: int = 10
    
chatbot_config = ChatBotConfig()

    
    
    