from flask import Flask, request, jsonify
import os
from utils.processor import process_config
import json
import logging
import boto3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Ensure required directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('results', exist_ok=True)

# Configure S3 client
s3_client = boto3.client('s3', region_name='ap-south-1')
bucket_name = 'processingdatatodownload'

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
        if os.path.exists(config_path):
            os.remove(config_path)
        if os.path.exists(zip_path):
            os.remove(zip_path)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)