from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import shutil
import time

app = Flask(__name__)

# Server par folder jahan files temporary save hongi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

# Folder saaf karne ka function (taki purani files na jama hon)
def clean_folder():
    if os.path.exists(DOWNLOAD_FOLDER):
        shutil.rmtree(DOWNLOAD_FOLDER)
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_media():
    clean_folder()  # Har naye download se pehle folder saaf karein
    
    url = request.form.get('url')
    mode = request.form.get('mode')  # single_video, single_audio, playlist, batch
    quality = request.form.get('quality', 'best')
    batch_urls = request.form.get('batch_urls') # Batch mode ke liye text area

    # Common Options
    ydl_opts = {
           'cookiefile': 'cookies.txt',  # <--- YEH LINE ADD KARNI HAI
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'restrictfilenames': True,  # Special characters hatane ke liye
    }

    # --- MODE 1: SINGLE VIDEO ---
    if mode == 'single_video':
        # Quality Map (Jo aapne script me diya tha)
        quality_map = {
            "360": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "best": "bestvideo+bestaudio/best"
        }
        ydl_opts['format'] = quality_map.get(quality, 'bestvideo+bestaudio/best')
        ydl_opts['merge_output_format'] = 'mp4'

    # --- MODE 2: SINGLE AUDIO ---
    elif mode == 'single_audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]

    # --- MODE 3: PLAYLIST (ZIP Banega) ---
    elif mode == 'playlist_video' or mode == 'playlist_audio':
        if mode == 'playlist_audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
        else:
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best' # Playlist ke liye 720p safe hai
            ydl_opts['merge_output_format'] = 'mp4'
        
        # Playlist folder structure
        ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_FOLDER, '%(playlist_index)s-%(title)s.%(ext)s')

    # --- MODE 4: BATCH DOWNLOAD (ZIP Banega) ---
    elif mode == 'batch':
        # Batch me hum URLs text area se lenge
        url_list = [u.strip() for u in batch_urls.split('\n') if u.strip()]
        if not url_list:
            return "Error: Koi URL nahi mila batch box me."
        
        # Batch ke liye best quality default
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
        
        # URL variable ko override kar denge list se process karne ke liye
        # Note: yt-dlp python library list accept karti hai
        url = url_list

    # --- EXECUTION ---
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Agar batch hai to list paas karein, warna single string
            if mode == 'batch':
                ydl.download(url) # Batch list download
            else:
                ydl.download([url])

        # --- FILE SENDING LOGIC ---
        
        # Agar Playlist ya Batch hai -> ZIP banao
        if mode in ['playlist_video', 'playlist_audio', 'batch']:
            shutil.make_archive(os.path.join(BASE_DIR, 'files'), 'zip', DOWNLOAD_FOLDER)
            return send_file(os.path.join(BASE_DIR, 'files.zip'), as_attachment=True)
        
        # Agar Single File hai -> Direct File bhejo
        else:
            files = os.listdir(DOWNLOAD_FOLDER)
            if files:
                filepath = os.path.join(DOWNLOAD_FOLDER, files[0])
                return send_file(filepath, as_attachment=True)
            else:
                return "Error: File download nahi ho payi."

    except Exception as e:
        return f"Error aaya: {str(e)}"

if __name__ == '__main__':
    app.run()
  
