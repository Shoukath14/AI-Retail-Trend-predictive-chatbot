import os
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add backend dir to path
sys.path.insert(0, os.path.dirname(__file__))

from models.db import init_db
from routes.chat import chat_bp
from routes.analysis import analysis_bp

app = Flask(__name__,
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend'),
            static_url_path='')

CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(analysis_bp)

# Initialize DB at startup — runs under both gunicorn (Render) and python app.py
init_db()

# Serve frontend — single-page app, all routing done by JS
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Catch-all: serve index.html for any unknown frontend path
@app.route('/<path:path>')
def catch_all(path):
    # Try to serve the file if it exists (e.g., styles.css, script.js)
    full = os.path.join(app.static_folder, path)
    if os.path.isfile(full):
        return send_from_directory(app.static_folder, path)
    # Otherwise fall back to SPA
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health():
    return {'status': 'ok', 'version': '1.0.0'}

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    print(f"🚀 AI Retail Trend Analyzer running at http://localhost:{port}")
    app.run(debug=debug, port=port, host='0.0.0.0')