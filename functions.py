import json
import os
from docx import Document

def read_knowledge_file(file_path):
    """Leer el contenido del archivo knowledge.docx"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo {file_path} no fue encontrado.")

    doc = Document(file_path)
    content = ""
    for para in doc.paragraphs:
        content += para.text + "\n"

    return content

def create_assistant(client):
    assistant_file_path = 'assistant.json'
    knowledge_file_path = 'knowledge.docx'  # Ruta del archivo de conocimiento

    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant ID.")
    else:
        # Leer el contenido del archivo de conocimiento
        knowledge_content = read_knowledge_file(knowledge_file_path)

        # Crear asistente con el contenido del archivo knowledge.docx
        assistant = client.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": knowledge_content}
            ]
        )

        with open(assistant_file_path, 'w') as file:
            json.dump({'assistant_id': assistant['id']}, file)
            print("Created a new assistant and saved the ID.")

        assistant_id = assistant['id']

    return assistant_id

