import os
import requests
import yt_dlp
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

app = Flask(__name__)

# --- CONFIGURATION ---
def get_ydl_opts():
    """Returns options with anti-bot headers and cookie support."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'simulate': True,  # Sirf info nikalo, download mat karo
        'format': 'best',  
        'ignoreerrors': True, # Error aaye toh crash mat hona
        'no_color': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Mode': 'navigate',
        }
    }
    # Agar cookies.txt server pe upload ki hai toh use karo
    if os.path.exists('cookies.txt'):
        opts['cookiefile'] = 'cookies.txt'
    return opts

def clean_resolution(f):
    """
    Format data se saaf resolution nikalne ka logic.
    Ex: '1920x1080' -> '1080p'
    """
    # 1. Height check karo (Sabse accurate)
    if f.get('height'):
        return f"{f['height']}p"
    
    # 2. Agar height nahi hai, resolution string check karo
    res_str = f.get('resolution')
    if res_str:
        # "1280x720" jaisa kuch ho toh "x" ke baad wala hissa lo
        if 'x' in res_str:
            return f"{res_str.split('x')[-1]}p"
        return res_str
    
    return "Unknown Quality"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/fetch_info', methods=['POST'])
def fetch_info():
    url = request.form.get('url')
    
    # 1. Input Validation
    if not url:
        return jsonify({'status': 'error', 'message': 'Please paste a link first!'})
    
    # 2. YouTube Blocking
    if "youtube.com" in url or "youtu.be" in url:
        return jsonify({'status': 'error', 'message': '🚫 YouTube downloads are not supported.'})

    try:
        with yt_dlp.YoutubeDL(get_ydl_opts()) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Agar info empty hai (Block ho gaya)
            if not info:
                return jsonify({'status': 'error', 'message': 'Failed to fetch video. Please try again.'})

            # --- PLAYLIST / MULTI-VIDEO HANDLING ---
            # Kabhi kabhi 'formats' direct nahi hote, 'entries' me hote hain
            if 'entries' in info:
                # Pehli video utha lo
                info = info['entries'][0]

            formats_list = []
            seen_res = set() # Duplicate quality hatane ke liye

            # --- FORMAT PARSING LOOP ---
            all_formats = info.get('formats', [])
            for f in reversed(all_formats):
                # Sirf wo link lo jisme Video Codec (vcodec) ho aur URL valid ho
                if f.get('url') and f.get('vcodec') != 'none':
                    
                    # Resolution saaf karo
                    res = clean_resolution(f)
                    
                    # Duplicate check
                    if res not in seen_res and res != "Unknown Quality":
                        # Size calculation
                        size = f.get('filesize') or f.get('filesize_approx')
                        size_str = f"{round(size / 1024 / 1024, 1)} MB" if size else "Size N/A"

                        formats_list.append({
                            'quality': res,
                            'ext': f.get('ext', 'mp4'),
                            'size': size_str,
                            'url': f['url']
                        })
                        seen_res.add(res)

            # Fallback: Agar upar wala logic fail ho jaye aur list khali reh jaye
            if not formats_list and info.get('url'):
                 formats_list.append({
                     'quality': 'Best Quality', 
                     'ext': 'mp4', 
                     'size': 'N/A', 
                     'url': info['url']
                 })

            return jsonify({
                'status': 'success',
                'title': info.get('title', 'Video Download'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration_string', ''),
                'formats': formats_list
            })

    except Exception as e:
        error_msg = str(e)
        # Technical error ko user friendly banao
        if "403" in error_msg: 
            return jsonify({'status': 'error', 'message': 'Access Denied. Try updating cookies.'})
        return jsonify({'status': 'error', 'message': f"Error: {error_msg}"})

@app.route('/proxy_download')
def proxy_download():
    """Server-side streaming to avoid CORS/IP blocks"""
    file_url = request.args.get('url')
    filename = request.args.get('filename', 'video.mp4')
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        # Stream=True zaroori hai
        req = requests.get(file_url, stream=True, headers=headers, timeout=20)
        return Response(
            stream_with_context(req.iter_content(chunk_size=4096)),
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": req.headers.get('content-type', 'video/mp4')
            }
        )
    except Exception:
        return "Download Failed. Link expired or blocked.", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
    
