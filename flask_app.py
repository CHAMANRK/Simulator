from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import shutil

app = Flask(__name__)

# Server paths setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloads')

def clean_folder():
    if os.path.exists(DOWNLOAD_FOLDER):
        shutil.rmtree(DOWNLOAD_FOLDER)
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_media():
    clean_folder()
    
    url = request.form.get('url')
    mode = request.form.get('mode')
    quality = request.form.get('quality', 'best')
    batch_urls = request.form.get('batch_urls')

    # --- SETTINGS (Isme Cookie file sahi se lagi hai) ---
    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'restrictfilenames': True,
    }

    # --- MODES ---
    if mode == 'single_video':
        quality_map = {
            "360": "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "480": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "720": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "1080": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "best": "bestvideo+bestaudio/best"
        }
        ydl_opts['format'] = quality_map.get(quality, 'bestvideo+bestaudio/best')
        ydl_opts['merge_output_format'] = 'mp4'

    elif mode == 'single_audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]

    elif mode == 'images':
        ydl_opts['skip_download'] = True
        ydl_opts['writethumbnail'] = True
        ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')

    elif mode in ['playlist_video', 'playlist_audio']:
        if mode == 'playlist_audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]
        else:
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_FOLDER, '%(playlist_index)s-%(title)s.%(ext)s')

    elif mode == 'batch':
        url_list = [u.strip() for u in batch_urls.split('\n') if u.strip()]
        if not url_list: return "Error: No URLs found"
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'
        url = url_list

    # --- DOWNLOAD EXECUTION ---
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if mode == 'batch':
                ydl.download(url)
            else:
                ydl.download([url])

        # --- SEND FILE ---
        if mode in ['playlist_video', 'playlist_audio', 'batch', 'images']:
            shutil.make_archive(os.path.join(BASE_DIR, 'files'), 'zip', DOWNLOAD_FOLDER)
            return send_file(os.path.join(BASE_DIR, 'files.zip'), as_attachment=True)
        else:
            files = os.listdir(DOWNLOAD_FOLDER)
            if files:
                return send_file(os.path.join(DOWNLOAD_FOLDER, files[0]), as_attachment=True)
            else:
                return "Error: Download failed (No file found)"

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
