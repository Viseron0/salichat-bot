#!/usr/bin/env python3
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

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

OPENAI_API_KEY = get_openai_api_key()
openai.api_key = OPENAI_API_KEY

#google sheets setup
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

def agregar_input(input_data):
    try:
        sheet.append_row(input_data)
        print(f"Input agregado a Google Sheets: {input_data}")
    except Exception as e:
        print(f"Error adding input to Google Sheets: {e}")

# usar el assistant_id de functions.py
assistant_id = functions.create_assistant(openai)

# Endpoint para iniciar conversación
@app.route('/start', methods=['GET'])
def start_conversation():
    logging.info("Starting a new conversation...")

    # Crear un nuevo thread
    thread = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Start a conversation."}],
        max_tokens=2048
    )
    logging.info(f"New thread created with ID: {thread.id}")
    return jsonify({"thread_id": thread.id})

# Generar respuesta en el chat
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')

    logging.info(f"Data received: {data}")

    if not thread_id:
        logging.error("Error: Missing thread_id")
        return jsonify({"error": "Missing thread_id"}), 400

    try:

     logging.info(f"Received message: {user_input} for thread ID: {thread_id}")  # Debugging line
     response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are interacting with a legal assistant that uses a knowledge base."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=2048
        )

     assistant_response = response['choices'][0]['message']['content']
     logging.info(f"Assistant response: {assistant_response}")

        # Guardar interacción en Google Sheets
     current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
     input_data = [thread_id, user_input, assistant_response, current_datetime]
     agregar_input(input_data)

     return jsonify({"response": assistant_response})

    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": "An error occurred"}), 500

# Run server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
