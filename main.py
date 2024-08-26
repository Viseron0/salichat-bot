#!/usr/bin/env python3
import os
from time import sleep
from packaging import version
from flask import Flask, request, jsonify
import openai
from openai import OpenAI
import functions
from google.cloud import secretmanager
import logging
from time import sleep
from datetime import datetime


app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')



#importar bibliotecas
try:
        import gspread
        from google.oauth2.service_account import Credentials
        SCOPES = ['https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/spreadsheets']
        CREDENTIALS_FILE = '/home/cloud/sali/salichat-credenciales.json'
        print("Bibliotecas importadas correctamente")
except ImportError as e:
        print(f"Error importing libraries: {e}")
        raise e


#acceso a los secretos de api key de secret manager de google
def access_secret_version(secret_name):
    """
    Accede a una versión de un secreto en Secret Manager.
    Args:
    secret_name (str): El nombre completo del recurso secreto.
    Returns:
    str: El valor del secreto como una cadena de texto.
    """
    client = secretmanager.SecretManagerServiceClient()
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode('UTF-8')

# Asume que 'your-secret-id' es el nombre del secreto donde has almacenado tu OPENAI_API_KEY
# y 'your-project-id' es tu ID de proyecto en GCP
secret_name = "projects/salichat/secrets/openai_api_key/versions/latest"
OPENAI_API_KEY = access_secret_version(secret_name)


# Configuración de Google Sheets
#CREDENTIALS_FILE = '/home/cloud/sali/salichat-credenciales.json'  # Ruta a tu archivo de credenciales JSON
try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client_gs = gspread.authorize(creds)
        print("Credenciales de Google Sheets configuradas correctamente")
        SHEET_ID = '1YJbLia2JBShRTWHzmOiZiW4E67WCEJ192bUhtDZt7_U'
        sheet = client_gs.open_by_key(SHEET_ID).sheet1  # Reemplaza con el nombre de tu Google Sheet
        print("Conexión a google sheets establecida")

except FileNotFoundError as e:
    print(f"Error setting up google sheets: {e}")
    raise e
except gspread.exceptions.APIError as e:
    print(f"API error: {e}")
    raise e
except gspread.exceptions.SpreadsheetNotFound as e:
    print(f"Spreadsheet not found: {e}")
    raise e



def agregar_input(input_data):
        try:
                sheet.append_row(input_data)
                print(F"Input agregado a google Sheets:{input_data}")
        except Exception as e:
                print(f"Error adding input to google sheets: {e}")


# Check OpenAI version is correct
required_version = version.parse("1.1.1")
current_version = version.parse(openai.__version__)
#OPENAI_API_KEY = os.environ['openai_api_key']
if current_version < required_version:
  raise ValueError(f"Error: OpenAI version {openai.__version__}"
                   " is less than the required version 1.1.1")
else:
  print("OpenAI version is compatible.")

# Start Flask app
app = Flask(__name__)

# Init client
client = OpenAI(api_key=OPENAI_API_KEY)  # should use env variable OPENAI_API_KEY in secrets (bottom left corner)

# Create new assistant or load existing
assistant_id = functions.create_assistant(client)

# Start conversation thread
@app.route('/start', methods=['GET'])
def start_conversation():
    logging.info("Starting a new conversation...")  # Debugging line
    thread = client.beta.threads.create()
    logging.info(f"New thread created with ID: {thread.id}")  # Debugging line
    return jsonify({"thread_id": thread.id})



# Generate response
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')

    logging.info(f"Data received: {data}")  # Log para verificar los datos recibidos

    if not thread_id:
        logging.error("Error: Missing thread_id")  # Debugging line
        return jsonify({"error": "Missing thread_id"}), 400

    logging.info(f"Received message: {user_input} for thread ID: {thread_id}")  # Debugging line

    try:
        # Add the user's message to the thread
        client.beta.threads.messages.create(thread_id=thread_id,
                                            role="user",
                                            content=user_input)

        logging.info("User message added to the thread")

        # Run the Assistant
        run = client.beta.threads.runs.create(thread_id=thread_id,
                                              assistant_id=assistant_id)

        logging.info(f"Assistant run started with ID: {run.id}")

        # Check if the Run requires action (function call)
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread_id,
                                                           run_id=run.id)
            logging.info(f"Run status: {run_status.status}")
            if run_status.status == 'completed':
                break
            sleep(1)  # Wait for a second before checking again

        # Retrieve and return the latest message from the assistant
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        response = messages.data[0].content[0].text.value

        logging.info(f"Assistant response: {response}")  # Debugging line

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        input_data = [thread_id, user_input, response,current_datetime]
        agregar_input(input_data)
        logging.info(f"Data saved to Google Sheets: {input_data}")

        return jsonify({"response": response,"datetime": current_datetime})

    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred"}), 500

# Run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
