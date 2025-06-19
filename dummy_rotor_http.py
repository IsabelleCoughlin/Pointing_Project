from http.server import BaseHTTPRequestHandler, HTTPServer
import json

# Simulated rotor state
rotor_state = {
    "azimuth": 0.0,
    "elevation": 0.0,
    "status": "stopped"
}

class DummyRotorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/rotor/position":
            # Return the current rotor position
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(rotor_state).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        if self.path == "/rotor/position":
            # Update rotor position
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                rotor_state["azimuth"] = data.get("azimuth", rotor_state["azimuth"])
                rotor_state["elevation"] = data.get("elevation", rotor_state["elevation"])
                rotor_state["status"] = "moving"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Position updated"}).encode("utf-8"))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        elif self.path == "/rotor/stop":
            # Simulate stopping the rotor
            rotor_state["status"] = "stopped"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Rotor stopped"}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

def run(server_class=HTTPServer, handler_class=DummyRotorHandler, port=4533):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting dummy rotor server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run()