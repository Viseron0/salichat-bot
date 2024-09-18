import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_conversation_from_google_sheets(sheet_url):
    # Conéctate a la hoja de Google Sheets y obtén el historial de la conversación
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('salichat-credenciales.json', scope)
    client = gspread.authorize(creds)

    # Abre la hoja de Google Sheets por URL
    sheet = client.open_by_url(sheet_url).sheet1

    # Obtener todos los registros (filas) de la hoja
    conversation_data = sheet.get_all_values()

    # Convierte los datos en un formato de texto para enviar por correo
    conversation_text = ""
    for row in conversation_data:
        conversation_text += " - ".join(row) + "\n"

    return conversation_text

def send_email(to_email, subject, message_body):
    # Configura la información del correo
    from_email = os.getenv("cloud@right-now.com.co")
    password = os.getenv("Issitjgtx1348")

    # Crea el mensaje
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Adjunta el cuerpo del mensaje
    msg.attach(MIMEText(message_body, 'plain'))

    # Inicia el servidor SMTP para enviar el correo
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

def send_conversation_history(sheet_url, user_email):
    conversation_history = get_conversation_from_google_sheets(sheet_url)
    subject = "Historial de tu conversación"
    send_email(user_email, subject, conversation_history)

