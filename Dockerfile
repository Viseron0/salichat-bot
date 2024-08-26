# Usar una imagen base de Python
FROM python:3.9-slim

# Crear un directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos de tu proyecto al contenedor
COPY . /app

# Instalar dependencias necesarias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto que usará la aplicación (ajusta si es necesario)
EXPOSE 8080

# Comando para ejecutar tu aplicación
CMD ["python", "main.py"]