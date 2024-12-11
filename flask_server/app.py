from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from utils.processor import process_config
import json
import logging
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Range", "X-Content-Range"]
    }
})

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

# Ensure required directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

# Configure S3 client
s3_client = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'processingdatatodownload'

@app.route('/process', methods=['POST'])
def process():
    config_path = None
    zip_path = None
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
        
        # Upload the zip file to S3
        s3_key = os.path.basename(zip_path)
        s3_client.upload_file(zip_path, bucket_name, s3_key)
        
        # Generate the S3 file URL
        s3_url = f"https://{bucket_name}.s3.ap-south-1.amazonaws.com/{s3_key}"
        
        return jsonify({'s3_url': s3_url}), 200
            
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Cleanup
        if config_path and os.path.exists(config_path):
            os.remove(config_path)
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'status': 'online',
        'endpoints': {
            '/process': 'POST - Process band arithmetic',
            '/health': 'GET - Health check'
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)