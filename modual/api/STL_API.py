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
    """Retrieves the indexed list of all models from the SQL database to populate the UI."""
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
                "mock_image_url": f"https://picsum.photos/seed/{item.id}/300/200"
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
    This function is use for testing and testing only it need to not be in the end version. The UI should not be
    requesting files directly. we should be giving it what it need
    :return:
    """
    print('model fetch requested')
    MODEL_DATABASE = {
        "1": r"D:\wh40k\space_marines\lt-titus\one_piece.stl",
        "2": r"D:\wh40k\space_marines\another-marine.stl"
    }
    data = request.get_json()

    # 1. Validate that the request has JSON data
    if not data or 'model_id' not in data:
        return jsonify({"error": "Missing model_id in request body"}), 400

    model_id = str(data['model_id'])
    print(model_id)

    # 2. Check if the ID exists in our allowed map
    if model_id not in MODEL_DATABASE:
        print('did not work')
        return jsonify({"error": "Model not found or access denied"}), 00

    actual_path = MODEL_DATABASE[model_id]

    # 3. Verify the file physically exists on the OS before trying to send it
    if not os.path.exists(actual_path):
        print('file did not exist')
        return jsonify({"error": "File missing on server drive"}), 404

    # Python safely streams the file data back to the browser
    print('sent')
    return send_file(actual_path, as_attachment=True)

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