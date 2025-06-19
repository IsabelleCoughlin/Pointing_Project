from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_data():
    data = request.json
    print("Received data:", data)
    # You can add code to log or process radiometer/spectrometer here
    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
