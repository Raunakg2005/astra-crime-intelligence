from .configs import chatbot_config
from .tools import all_tools
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

SYSTEM_PROMPT = """You are Astra, an analytics assistant embedded in the KSP Crime \
Intelligence dashboard. You help police analysts query crime statistics, hotspots, \
predictive risk, offender networks, and FIR narrative classification.

Rules:
- Always answer using a tool call. Never state a statistic, count, or name from memory.
- If a question needs more than one tool (e.g. comparing districts and their risk), call \
each tool needed before answering.
- State the data's date range (from get_kpis) when giving headline numbers, so answers \
are clearly dated.
- If a tool call fails or returns no data, say so plainly instead of guessing.
- Reply in plain text only — no markdown (no **bold**, no #headers, no bullet dashes). \
The UI renders your response as-is, so formatting characters would show up literally.
"""


class ChatBot:
    def __init__(self):
        self.configs = chatbot_config
        self.setup_completed = False
        self.agent = None
        self._setup()
        
    def _setup(self):
        try:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            groq_api_key = os.getenv("GROQ_API_KEY")
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY is not set in the environment variables.")

            self.agent = create_agent(
                cache=True,
                model=f"groq:{self.configs.model_name}",
                tools=all_tools,
                checkpointer=InMemorySaver(),
                system_prompt=SYSTEM_PROMPT,
            )
            
            print("Chatbot setup completed successfully.")
            self.setup_completed = True
        except Exception as e:
            print(f"Error during setup: {e}")
            raise e
    