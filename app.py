from flask import Flask, request, send_file
import yt_dlp
import os

app = Flask(__name__)

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url: return "Missing URL", 400

    output = '/tmp/video.mp4'
    ydl_opts = {'format': 'best', 'outtmpl': output, 'quiet': True}

    try:
        if os.path.exists(output): os.remove(output)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return send_file(output, as_attachment=True)
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run()