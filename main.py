import os
from time import sleep
from packaging import version
from flask import Flask, request, jsonify
import openai
from apikey_service import get_openai_api_key  # Importa la función de apikey_service
import functions
import logging
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import uuid

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Obtener la API Key desde la variable de entorno usando apikey_service
OPENAI_API_KEY = get_openai_api_key()
openai.api_key = OPENAI_API_KEY

# Configuración de Google Sheets usando el archivo de credenciales
try:
    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

    CREDENTIALS_FILE = '/home/ec2-user/salichat-bot/salichat-credenciales.json'

    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client_gs = gspread.authorize(creds)
    print("Credenciales de Google Sheets configuradas correctamente")

    SHEET_ID = '1YJbLia2JBShRTWHzmOiZiW4E67WCEJ192bUhtDZt7_U'
    sheet = client_gs.open_by_key(SHEET_ID).sheet1
    print("Conexión a Google Sheets establecida")

except FileNotFoundError as e:
    print(f"Error setting up Google Sheets: {e}")
    raise e
except gspread.exceptions.APIError as e:
    print(f"API error: {e}")
    raise e
except gspread.exceptions.SpreadsheetNotFound as e:
    print(f"Spreadsheet not found: {e}")
    raise e

# Función para agregar datos a Google Sheets
def agregar_input(input_data):
    try:
        sheet.append_row(input_data)
        print(f"Input agregado a Google Sheets: {input_data}")
    except Exception as e:
        print(f"Error adding input to Google Sheets: {e}")


conversations = {}

# Endpoint para iniciar conversación
@app.route('/start', methods=['GET'])
def start_conversation():

   try:
      conversation_id = str(uuid.uuid4())
      print(openai.__version__)
      print(conversation_id)
      response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",  # Usa un modelo compatible
          messages=[
              {"role": "user", "content": "Start a conversation."}
          ]
      )
        # Devuelve la respuesta de OpenAI en formato JSON
      return jsonify(response['choices'][0]['message']['content'])


   except Exception as e:
      return jsonify({"error": str(e)}), 500



# Generar respuesta
@app.route('/chat', methods=['POST'])
def chat():
    logging.info(f"Request Headers: {request.headers}")
    logging.info(f"Request Content-Type: {request.content_type}")
    logging.info(f"Request Data: {request.data}")

    if not request.is_json:
        logging.error("Error: Unsupported Media Type - Content-Type must be application/json")
        return jsonify({"error": "Unsupported Media Type - Content-Type must be application/json"}), 415

    data = request.json
    thread_id = data.get('thread_id')
    print(thread_id)
    user_input = data.get('message', '')

    logging.info(f"Data received: {data}")

    if not thread_id:
        logging.error("Error: Missing thread_id")
        return jsonify({"error": "Missing thread_id"}), 400

    logging.info(f"Received message: {user_input} for thread ID: {thread_id}")


    if thread_id not in conversations:
        conversations[thread_id] = []

    conversation_history = conversations[thread_id]
    conversation_history.append({"role": "user", "content": user_input})



    try:

       # Enviar el mensaje del usuario a la API de OpenAI y obtener respuesta
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        )

        # Obtener el contenido de la respuesta generada
        assistant_response = response['choices'][0]['message']['content']
        logging.info(f"Assistant response: {assistant_response}")
        conversation_history.append({"role": "assistant", "content": assistant_response})

        # Guardar el registro de la interacción con la fecha y hora actual
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        input_data = [thread_id, user_input, assistant_response, current_datetime]
        agregar_input(input_data)  # Asumiendo que esta función guarda en Google Sheets
        logging.info(f"Data saved to Google Sheets: {input_data}")

        # Devolver la respuesta del asistente al cliente
        return jsonify({"response": assistant_response})

    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred"}), 500

# Ejecutar el servidor
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)


