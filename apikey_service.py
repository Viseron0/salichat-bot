import os

# Obtener la API key de OpenAI desde la variable de entorno
def get_openai_api_key():
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not openai_api_key:
        raise ValueError("La API Key de OpenAI no está configurada en las variables de entorno.")

    return openai_api_key
