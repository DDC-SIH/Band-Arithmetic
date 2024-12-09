
from flask import Flask, request, send_file, jsonify
import os
from utils.processor import process_config
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure required directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

@app.route('/process', methods=['POST'])
def process():
    try:
        # Get JSON data from request
        config_data = request.get_json()
        if not config_data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Save config to temporary file
        config_path = os.path.join('uploads', 'temp_config.json')
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Process the config
        zip_path = process_config(config_path)
        
        # Send the zip file
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name='cropped_results.zip'
        )
            
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup
        if os.path.exists(config_path):
            os.remove(config_path)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)