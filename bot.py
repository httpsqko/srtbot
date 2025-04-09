import telebot
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Reemplaza 'TU_TOKEN_AQUÍ' con el token que te dio BotFather
bot = telebot.TeleBot('7689202374:AAHvUCW7GYODJ-hbXPPP4yLTHF2SlEyO4_0')

# Comando /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "¡Hola! Envíame un enlace de YouTube y te extraeré los subtítulos en formato SRT.")

# Manejar mensajes con enlaces de YouTube
@bot.message_handler(func=lambda message: 'youtube.com' in message.text or 'youtu.be' in message.text)
def handle_youtube_link(message):
    try:
        # Extraer el ID del video del enlace
        url = message.text
        video_id = extract_video_id(url)
        
        if not video_id:
            bot.reply_to(message, "No pude encontrar un ID válido en el enlace. Asegúrate de enviar un enlace de YouTube correcto.")
            return
        
        # Obtener los subtítulos
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es', 'en'])  # Prioriza español, luego inglés
        
        # Convertir a formato SRT
        srt_content = transcript_to_srt(transcript)
        
        # Guardar en un archivo SRT
        srt_filename = f"{video_id}.srt"
        with open(srt_filename, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        # Enviar el archivo al usuario
        with open(srt_filename, 'rb') as srt_file:
            bot.send_document(message.chat.id, srt_file)
        
        bot.reply_to(message, "¡Aquí tienes los subtítulos en formato SRT!")
    
    except Exception as e:
        bot.reply_to(message, f"Ocurrió un error: {str(e)}. Asegúrate de que el video tenga subtítulos disponibles.")

# Función para extraer el ID del video de YouTube
def extract_video_id(url):
    patterns = [
        r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})',  # youtube.com/watch?v=ID o youtu.be/ID
        r'(?:embed/)([a-zA-Z0-9_-]{11})'           # youtube.com/embed/ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# Función para convertir los subtítulos a formato SRT
def transcript_to_srt(transcript):
    srt_lines = []
    for i, item in enumerate(transcript, start=1):
        start_time = format_time(item['start'])
        end_time = format_time(item['start'] + item['duration'])
        text = item['text']
        srt_lines.append(f"{i}\n{start_time} --> {end_time}\n{text}\n")
    return '\n'.join(srt_lines)

# Función para formatear el tiempo al estilo SRT (00:00:00,000)
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# Iniciar el bot
bot.polling()