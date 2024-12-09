
from flask import Flask, request, send_file, jsonify
import os
from download import process_config
import json
import logging

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'

# Ensure upload and results directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route('/process', methods=['POST'])
def process():
    try:
        # Get JSON data from request
        config_data = request.get_json()
        
        # Save config to temporary file
        config_path = os.path.join(UPLOAD_FOLDER, 'temp_config.json')
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Process the config
        process_config(config_path)
        
        # Check if zip file was created
        zip_path = 'cropped_results.zip'
        if os.path.exists(zip_path):
            return send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name='cropped_results.zip'
            )
        else:
            return jsonify({'error': 'Processing failed'}), 500
            
    except Exception as e:
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