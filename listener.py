from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

@app.route('/sdrangel/deviceset/0/channel/0', methods=['POST'])
def handle_reverse_api_data():
    data = request.get_json()
    print(f"[{datetime.datetime.now()}] Received ReverseAPI data:")
    print(data)
    return jsonify({"status": "ok"})

#@app.route('/sdrangel/deviceset/0/channel/0', methods=['POST'])
#def handle_reverse_api_data():
#    content_type = request.content_type
#    print(f"Received POST with content-type: {content_type}")
#    
#    if content_type == 'application/json':
#        data = request.get_json()
#    else:
#        data = request.data  # raw bytes
#    
#    print(f"[{datetime.datetime.now()}] Received ReverseAPI data:")
#    print(data)
#    return jsonify({"status": "ok"})


@app.route('/sdrangel/deviceset/0/channel/0/settings', methods=['PATCH'])
def handle_patch_settings():
    data = request.get_json()
    print(f"[{datetime.datetime.now()}] Received PATCH settings:")
    print(data)
    return jsonify({"status": "patched"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
