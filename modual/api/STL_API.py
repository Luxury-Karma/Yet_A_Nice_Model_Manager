"""
@File: STL_API.py
@Project: modual\\api\\STL_API
@Author: Alexandre Gauvin
Handles request routing frameworks for rendering or updating 3D asset tables with tracking logs.
"""
import os
import sys
import threading
from flask import request, Flask, jsonify, send_file
from flask_cors import CORS
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from modual.sql.session_creator import session_local
from modual.sql.querry import model
from modual.sql.add_models_to_db import sync_directory_pipeline
from modual.file_finder import find_specific_directory

app = Flask(__name__)
CORS(app)

@app.route('/test', methods=['GET'])
def test():
    print("📡 [PING] Test endpoint hit by frontend!")
    return jsonify({'data': 'It is working!'})

@app.route('/get_stl', methods=['GET'])
def get_stl_list():
    """
    This function is returning the file so the web server can show both the file and the name
    :return: {
    "id": file id,
    "file_name": file name,
    "file_path": file path,
    "file_size": file size,
    "tags": tags,
    }, 200 if successful. Else error code
    """
    db = session_local()
    try:
        db_models = db.query(model).all()
        payload = []
        for item in db_models:
            tag_names = [t.name for t in item.tags] if hasattr(item, 'tags') and item.tags else []
            if not tag_names and item.file_name:
                tag_names = [item.file_name.split('.')[-1].upper()]

            payload.append({
                "id": item.id,
                "file_name": item.file_name,
                "file_path": item.file_path or "",
                "file_size": item.file_size or 0,
                "tags": tag_names,
            })
        return jsonify(payload), 200
    except Exception as e:
        print(f"❌ [DATABASE ERROR] Failed to fetch layout rows: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/fetch-model', methods=['POST'])
def fetch_model():
    """
    Give a specific model information
    format :
    {
        "model_id": model id,
    }
    """
    data = request.get_json()

    # 1. Validate incoming request body structure
    if not data or 'model_id' not in data:
        return jsonify({"error": "Missing model_id in request body"}), 400

    model_id = data['model_id']
    print(f"📦 [VERIFYING] Client requested binary stream for Model ID: {model_id}")

    db = session_local()
    try:
        # 2. Query the DB to verify the model exist
        target_model = db.query(model).filter(model.id == model_id).first()

        if not target_model:
            print(f"⚠️ [SECURITY ALERT] Requested Model ID {model_id} does not exist in the database.")
            return jsonify({"error": "Access denied or invalid model context."}), 403

        actual_path = target_model.file_path
        print(f"🔗 [PATH RESOLVED] Target path from database record: {actual_path}")

        # 4. Verify that the file physically exists on the OS drive
        if not os.path.exists(actual_path):
            print(f"❌ [IO ERROR] Database has record, but file is missing from drive: {actual_path}")
            return jsonify({"error": "File missing on server drive"}), 404

        # 5. Safe, validated binary file transmission
        print(f"🚀 [STREAMING] Sending verified bytes for {target_model.file_name}")
        return send_file(actual_path, as_attachment=True)

    except Exception as e:
        print(f"❌ [SERVER ERROR] Error processing file validation loop: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

def run_background_sync(target_directory):
    """Worker function tasked with performing the heavy storage drive crawling pass."""
    print("\n==================================================")
    print(f"🚀 [BACKGROUND THREAD] Starting drive scan now!")
    print(f"📂 Target Directory: {target_directory}")
    print("==================================================")

    try:
        # Runs the database insertion logic from your pipeline modules
        metrics = sync_directory_pipeline(target_directory)

        print("\n==================================================")
        print(f"✨ [BACKGROUND THREAD] Drive scan completed successfully!")
        print(f"   📊 Added: {metrics.get('added', 0)}")
        print(f"   ⏩ Skipped: {metrics.get('skipped', 0)}")
        print(f"   ❌ Failed: {metrics.get('failed', 0)}")
        print("==================================================\n")
    except Exception as e:
        print(f"\n❌ [BACKGROUND THREAD] Critical execution failure during crawl: {e}\n")


@app.route('/find_stl', methods=['POST'])
def find_all_stl():
    """Triggers a background directory scan and returns immediately to keep the UI responsive."""
    print("\n📥 [API HIT] GET /find_stl requested by frontend web client!")

    data = request.get_json()
    if not data:
        print("❌ [API ERROR] Received empty request body payload.")
        return jsonify({'error': 'Missing request body'}), 400

    print(f"📦 [API PAYLOAD] Received JSON data: {data}")

    target_directory = data.get('directory_path')
    if not target_directory:
        print("❌ [API ERROR] 'directory_path' key missing from JSON.")
        return jsonify({'error': 'Missing directory_path parameter in request body'}), 400

    if not os.path.isdir(target_directory):
        print(f"❌ [API ERROR] Path is not a valid directory on this machine: '{target_directory}'")
        return jsonify({'error': f'Provided path is not a valid directory: {target_directory}'}), 400

    print(f"🔄 [API ACTION] Path validated. Spawning background thread for crawler...")

    # Spin up the background worker thread so the server logs print while the UI returns instantly
    scan_thread = threading.Thread(
        target=run_background_sync,
        args=(target_directory,),
        daemon=True
    )
    scan_thread.start()

    print("📤 [API RESPONSE] Thread spawned. Sending 202 Accepted back to browser.")
    return jsonify({
        'status': 'scan_initiated',
        'message': f'Deep drive scan successfully initialized for {target_directory}. Assets will populate shortly.'
    }), 202


@app.route('/locate_directory', methods=['POST'])
def locate_directory():
    """
    allow the location of a directory for future search. So User can drag and drop files in
    format : {
    "folder_name": "WHAT EVER",
    "fingerprint": ["What", "Ever"],
    }
    :return: success or failure
    """
    request_json = request.get_json()
    if not request_json:
        return jsonify({'error': 'Missing request body'}), 400
    target_directory: str | None = request_json.get('folder_name')
    if not target_directory:
        return jsonify({'error': 'Missing directory_path parameter in request body'}), 400
    target_directory = find_specific_directory(target_directory,request_json.get('fingerprint'))

    if not isinstance(target_directory, str):
        return jsonify({'error': 'Could not find path'}), 400

    sync_directory_pipeline(target_directory)
    return jsonify({'success': True}), 202










if __name__ == '__main__':
    # Binds to 0.0.0.0 to guarantee local interface connections match up
    app.run(debug=True, host='0.0.0.0', port=5000)