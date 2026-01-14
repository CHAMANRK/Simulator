from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import yt_dlp
import requests
import urllib.parse

app = Flask(__name__)

# --- CONFIGURATION ---
def get_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'simulate': True,  # Download mat karo, sirf info do
        'cookiefile': 'cookies.txt',  # Optional: Agar login required ho
        # User Agent spoofing taaki Instagram/FB block na kare
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/fetch_info', methods=['POST'])
def fetch_info():
    url = request.form.get('url')
    
    # 1. YouTube Blocking Logic
    if "youtube.com" in url or "youtu.be" in url:
        return jsonify({'status': 'error', 'message': '🚫 YouTube downloads are restricted by policy.'})

    if not url:
        return jsonify({'status': 'error', 'message': 'Please enter a valid URL.'})

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Formats filter karna (Best quality aur alag alag resolutions)
            formats_list = []
            seen_qualities = set()

            # Reverse order taaki best quality pehle aaye
            for f in reversed(info.get('formats', [])):
                # Sirf MP4/Video formats uthao jo useful hon
                if f.get('vcodec') != 'none' and f.get('url'):
                    resolution = f.get('resolution', 'Unknown')
                    filesize = f.get('filesize_approx') or f.get('filesize')
                    
                    # Duplicate quality hatana
                    if resolution not in seen_qualities and resolution != 'audio only':
                        # Size convert (Bytes to MB)
                        size_mb = f"{round(filesize / 1024 / 1024, 2)} MB" if filesize else "N/A"
                        
                        formats_list.append({
                            'format_id': f['format_id'],
                            'quality': resolution,
                            'ext': f['ext'],
                            'size': size_mb,
                            'url': f['url'], # Original Direct Link
                            'type': 'video'
                        })
                        seen_qualities.add(resolution)
            
            # Audio Only option add karna
            formats_list.append({
                'quality': 'Audio Only (MP3/M4A)',
                'ext': 'mp3',
                'size': 'Auto',
                'url': url, # Hum proxy ke through audio convert nahi kar rahe abhi, simple rakha hai
                'type': 'audio',
                'is_audio_mode': True 
            })

            return jsonify({
                'status': 'success',
                'title': info.get('title', 'Video'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration_string'),
                'formats': formats_list
            })

    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Failed to fetch: {str(e)}"})

@app.route('/proxy_download')
def proxy_download():
    """
    Ye function 'Man in the Middle' banta hai.
    User -> Server -> Instagram/FB
    Isse IP restriction bypass hoti hai.
    """
    file_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    
    if not file_url:
        return "No URL provided", 400

    # Headers for request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Stream=True zaroori hai taaki server ki RAM na bhare
        req = requests.get(file_url, stream=True, headers=headers)
        
        return Response(
            stream_with_context(req.iter_content(chunk_size=4096)),
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": req.headers.get('content-type', 'video/mp4')
            }
        )
    except Exception as e:
        return f"Proxy Error: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
    
