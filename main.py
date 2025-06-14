from flask import Flask, request, jsonify, send_file
import yt_dlp
import os
import uuid
import subprocess

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp"

def download_video(url, format='best'):
    ydl_opts = {
        'format': format,
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
    return file_path, info

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data['url']
    format = data.get('format', 'best')
    try:
        file_path, info = download_video(url, format)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/mp3', methods=['POST'])
def mp3():
    data = request.json
    url = data['url']
    try:
        file_path, info = download_video(url, 'bestaudio')
        mp3_path = file_path.rsplit('.', 1)[0] + '.mp3'
        subprocess.run(['ffmpeg', '-i', file_path, mp3_path])
        return send_file(mp3_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/thumbnail', methods=['POST'])
def thumbnail():
    url = request.json['url']
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        thumbs = info.get('thumbnails', [])
    return jsonify({'thumbnails': thumbs})

@app.route('/tags', methods=['POST'])
def tags():
    url = request.json['url']
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        return jsonify({'tags': info.get('tags', [])})

@app.route('/playlist', methods=['POST'])
def playlist():
    url = request.json['url']
    ydl_opts = {'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return jsonify({'entries': info.get('entries', [])})

@app.route('/clip', methods=['POST'])
def clip():
    data = request.json
    url = data['url']
    start = data['start']
    end = data['end']
    try:
        file_path, info = download_video(url)
        output_path = file_path.rsplit('.', 1)[0] + '_clip.mp4'
        subprocess.run(['ffmpeg', '-ss', start, '-to', end, '-i', file_path, '-c', 'copy', output_path])
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/')
def home():
    return "YouTube Backend is running!"

if __name__ == '__main__':
    app.run()
