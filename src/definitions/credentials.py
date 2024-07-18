import os

from dotenv import load_dotenv

load_dotenv()


class Credentials:

    @classmethod
    def openai_api_key(cls) -> str:
        return os.getenv("OPENAI_API_KEY")

    @classmethod
    def retell_api_key(cls) -> str:
        return os.getenv("RETELL_API_KEY")

    @classmethod
    def retell_agent_id(cls) -> str:
        return os.getenv('RETELL_AGENT_ID')

    @classmethod
    def ngrok_ip_address(cls) -> str:
        # May not need this
        return os.getenv("NGROK_IP_ADDRESS")


class EnvVariables:
    @classmethod
    def chat_model(cls) -> str:
        return os.getenv("CHAT_MODEL")
