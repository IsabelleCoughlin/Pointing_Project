from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

def log_request(method, path, content_type, data):
    timestamp = datetime.datetime.now()
    print(f"[{timestamp}] {method} request on '/{path}' (Content-Type: {content_type})")
    print(f"[{timestamp}] Data:\n{data}\n")


@app.route('/sdrangel/deviceset/0/channel/0/settings', methods=['PATCH'])
def handle_patch_settings():
    try:
        content_type = request.content_type
        data = request.get_json()
        log_request("PATCH", "sdrangel/deviceset/0/channel/0/settings", content_type, data)
        return jsonify({"status": "patched"})
    except Exception as e:
        print(f"[ERROR PATCH] {e}")
        return jsonify({"status": "error"}), 500


@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def catch_all_post(path):
    try:
        content_type = request.content_type
        if content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.data
        log_request("POST", path, content_type, data)
        return jsonify({"status": "ok"})
    except Exception as e:
        print(f"[ERROR POST] {e}")
        return jsonify({"status": "error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
