# Usa una imagen base de Python
FROM python:3.8-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requisitos (requirements.txt) al directorio de trabajo
COPY requirements.txt requirements.txt

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Copia el contenido de la carpeta actual al directorio de trabajo en el contenedor
COPY . .

# Expone el puerto 5000 para que la aplicación Flask pueda ser accedida desde el exterior
EXPOSE 5000

# Define el comando que se ejecutará cuando el contenedor se inicie
CMD ["python", "app.py"]
