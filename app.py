from flask import Flask, jsonify, request, render_template, g
from flask_cors import CORS
from pymongo import MongoClient
from google.cloud import storage
from flask_redis import FlaskRedis
import os
from bson.objectid import ObjectId

app = Flask(__name__, template_folder='templates')
CORS(app)

# Configuración de la conexión a MongoDB
client = MongoClient('mongodb://user:T1kt0kcl0n_@34.23.237.38:27017/')
db = client['Examen3']
watch_times_collection = db['tiktok']
videos_collection = db['videos']

# Configuración de Redis
app.config['REDIS_URL'] = "redis://34.23.237.38:6379/0"
redis_client = FlaskRedis(app)

# Configuración de Google Cloud Storage
# Asegúrate de que la variable de entorno GOOGLE_APPLICATION_CREDENTIALS esté configurada
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './credenciales.json'  # Reemplaza con la ruta a tus credenciales

storage_client = storage.Client()
bucket_name = 'videos-tiktok'  # Reemplaza con tu bucket de Google Cloud Storage
bucket = storage_client.bucket(bucket_name)

# Ruta para subir videos a Google Cloud Storage y guardar la URL en MongoDB
#@app.route('/api/upload-video', methods=['POST'])
# def upload_video():
#    if 'file' not in request.files:
#        return jsonify({"error": "No file part"}), 400
    
#    file = request.files['file']
#    if file.filename == '':
#        return jsonify({"error": "No selected file"}), 400
    
    # Guardar el archivo en Google Cloud Storage
#    blob = bucket.blob(file.filename)
#    blob.upload_from_file(file)
    
    # Guardar la ruta en MongoDB
#    video_document = {
#        'filename': file.filename,
#        'url': blob.public_url
#    }
#    videos_collection.insert_one(video_document)
    
#    return jsonify({"message": "File uploaded successfully", "url": blob.public_url}), 201


# Variable global para almacenar el último ID utilizado
last_video_id = 0

@app.route('/api/upload-video', methods=['POST'])
def upload_video():
    global last_video_id  # Indica que vamos a usar la variable global
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Guardar el archivo en Google Cloud Storage
    blob = bucket.blob(file.filename)
    blob.upload_from_file(file)
    
    # Incrementar el ID para el nuevo video
    last_video_id += 1
    
    # Guardar la ruta en MongoDB con el nuevo ID
    video_document = {
        'video_id': last_video_id,
        'filename': file.filename,
        'url': blob.public_url
    }
    videos_collection.insert_one(video_document)
    
    return jsonify({"message": "File uploaded successfully", "url": blob.public_url, "video_id": last_video_id}), 201

# Ruta para recibir los datos de tiempo de visualización
@app.route('/api/video-watch-time', methods=['POST'])
def receive_watch_time():
    data = request.json
    video_id = data['video_id']
    watch_time = data['watch_time']
    print(f"Video ID: {video_id}, Watch Time: {watch_time} seconds")
    watch_times_collection.insert_one({'video_id': video_id, 'watch_time': watch_time})
    return jsonify({'message': 'Watch time received'}), 200

# Ruta para obtener todos los tiempos de visualización almacenados
@app.route('/api/watch-times', methods=['GET'])
def get_watch_times():
    watch_times = list(watch_times_collection.find({}, {'_id': 0}))
    return jsonify(watch_times), 200

# Ruta para obtener todas las URL de los videos almacenados

@app.route('/api/videos', methods=['GET'])
def get_videos():
    cached_videos = redis_client.get('videos')
    if cached_videos:
        return jsonify({"videos": eval(cached_videos.decode('utf-8'))})  # Uso de eval para convertir la cadena a lista

    videos = list(videos_collection.find({}, {'_id': 0, 'filename': 1, 'url': 1}))
    redis_client.set('videos', str(videos))
    return jsonify({"videos": videos})

import base64
import requests

@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video_by_id(video_id):
    video = videos_collection.find_one({'video_id': int(video_id)}, {'_id': 0, 'filename': 1, 'url': 1})
    if video:
        cached_video = redis_client.get(str(video_id))
        if cached_video:
            video_data = cached_video.decode('utf-8')
        else:
            video_url = video['url']
            response = requests.get(video_url)
            if response.status_code == 200:
                video_data = base64.b64encode(response.content).decode('utf-8')
                redis_client.set(str(video_id), video_data)
            else:
                return jsonify({"message": "Failed to fetch video"}), 500
        return render_template('video_player.html', video_data=video_data)
    else:
        return jsonify({"message": "Video not found"}), 404



if __name__ == '__main__':
    app.run(debug=True)