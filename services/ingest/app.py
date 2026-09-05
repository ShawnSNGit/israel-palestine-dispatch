from flask import Flask, request, jsonify
from pathlib import Path
import hashlib
import json

app = Flask(__name__)
DATA_DIR = Path('/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/enqueue', methods=['POST'])
def enqueue():
    body = request.get_json() or {}
    url = body.get('url')
    if not url:
        return jsonify({'error': 'missing url'}), 400
    # Minimal enqueue: write to file for local/dev; in prod push to queue (Kafka/SQS)
    key = hashlib.sha256(url.encode('utf-8')).hexdigest()
    entry = {'url': url}
    (DATA_DIR / f'{key}.json').write_text(json.dumps(entry), encoding='utf-8')
    return jsonify({'enqueued': True, 'key': key})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
