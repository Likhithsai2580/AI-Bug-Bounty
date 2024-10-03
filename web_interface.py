from flask import Flask, render_template, request, jsonify, url_for
from main import main as run_scan
import asyncio

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    target_url = request.json['target_url']
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run_scan(target_url))
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)