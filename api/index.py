import telebot
from youtube_transcript_api import YouTubeTranscriptApi
import re
from flask import Flask, request, Response

# Crea una aplicación Flask
app = Flask(__name__)

# Configura el bot con tu token
TOKEN = '7689202374:AAHvUCW7GYODJ-hbXPPP4yLTHF2SlEyO4_0'
bot = telebot.TeleBot(TOKEN)

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Envíame un enlace de YouTube y te extraeré los subtítulos en formato SRT.")

# Manejar mensajes con enlaces de YouTube
@bot.message_handler(func=lambda message: 'youtube.com' in message.text or 'youtu.be' in message.text)
def handle_youtube_link(message):
    try:
        url = message.text
        video_id = extract_video_id(url)
        
        if not video_id:
            bot.reply_to(message, "No pude encontrar un ID válido en el enlace. Asegúrate de enviar un enlace de YouTube correcto.")
            return
        
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])
        srt_content = transcript_to_srt(transcript)
        
        srt_filename = f"/tmp/{video_id}.srt"  # Usamos /tmp para Vercel (sistema de archivos temporal)
        with open(srt_filename, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        with open(srt_filename, 'rb') as srt_file:
            bot.send_document(message.chat.id, srt_file)
        
        bot.reply_to(message, "¡Aquí tienes los subtítulos en formato SRT!")
    
    except Exception as e:
        bot.reply_to(message, f"Ocurrió un error: {str(e)}. Asegúrate de que el video tenga subtítulos disponibles.")

# Funciones auxiliares
def extract_video_id(url):
    patterns = [
        r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def transcript_to_srt(transcript):
    srt_lines = []
    for i, item in enumerate(transcript, start=1):
        start_time = format_time(item['start'])
        end_time = format_time(item['start'] + item['duration'])
        text = item['text']
        srt_lines.append(f"{i}\n{start_time} --> {end_time}\n{text}\n")
    return '\n'.join(srt_lines)

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# Ruta del webhook como función serverless
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return Response('OK', status=200)
    else:
        return Response('Error', status=400)

# Ruta raíz (opcional, para verificar que la API está viva)
@app.route('/')
def home():
    return "Bot activo"

# Esto es necesario para Vercel (exporta la app como una función serverless)
def handler(request):
    return app(request.environ, request.start_response)