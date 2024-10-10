from flask import Flask, render_template, request, jsonify, url_for
from main import main as run_scan
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    logger.debug("Rendering index.html")
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    logger.debug("Received POST request to /scan")
    target_url = request.json['target_url']
    logger.debug(f"Target URL: {target_url}")
    
    logger.debug("Creating new event loop")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    logger.debug("Running scan")
    result = loop.run_until_complete(run_scan(target_url))
    
    logger.debug(f"Scan result: {result}")
    return jsonify(result)

if __name__ == '__main__':
    logger.debug("Starting Flask app in debug mode")
    app.run(debug=True)