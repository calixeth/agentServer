import openai

from config import SETTINGS

openai_client = openai.AsyncClient(api_key=SETTINGS.OPENAI_API_KEY)
