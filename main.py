import json
import urllib.request
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class MockConfigServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path_parts = [p for p in self.path.strip("/").split("/") if p]
        if len(path_parts) >= 2:
            app_name = path_parts[0]
            profile = path_parts[1]
            response_data = {
                "name": app_name,
                "profiles": [profile],
                "label": "main",
                "version": "f2c019481a5e128912",
                "state": None,
                "propertySources": [
                    {
                        "name": f"https://github.com/foodx/config-repo.git/{app_name}-{profile}.yml",
                        "source": {
                            "server.port": 8081,
                            "spring.datasource.url": "jdbc:mysql://db-prod:3306/restaurant_db",
                            "logging.level.root": "INFO"
                        }
                    },
                    {
                        "name": f"https://github.com/foodx/config-repo.git/application.yml",
                        "source": {
                            "eureka.client.service-url.defaultZone": "http://localhost:8761/eureka/"
                        }
                    }
                ]
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json;charset=UTF-8")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode('utf-8'))
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Bad Request: Invalid Endpoint Format")

    def log_message(self, format, *args):
        # Suppress standard logging for cleaner output
        return

def run_simulation():
    print("============================================================")
    print("   KIỂM THỬ GIẢ LẬP VÀ XÁC NHẬN CẤU HÌNH CONFIG SERVER")
    print("============================================================")
    
    server_address = ('127.0.0.1', 8888)
    httpd = HTTPServer(server_address, MockConfigServerHandler)
    
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("[1] Mock Config Server dang chay tai http://localhost:8888")
    time.sleep(0.5)
    
    target_url = "http://127.0.0.1:8888/restaurant-service/prod"
    print(f"[2] Gui request tu restaurant-service: GET {target_url}")
    
    try:
        req = urllib.request.Request(target_url)
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            
            print(f"[3] Ket qua phan hoi tu Config Server (HTTP Status: {status}):")
            print("------------------------------------------------------------")
            print(body)
            print("------------------------------------------------------------")
            
            if status == 200 and "propertySources" in body:
                print("[SUCCESS] KIỂM THỬ THÀNH CÔNG! Config Server đã xử lý và trả cấu hình chính xác.")
            else:
                print("[ERROR] Phản hồi không đúng định dạng mong đợi.")
    except Exception as e:
        print(f"[ERROR] Khong the ket noi toi Config Server: {e}")
    finally:
        httpd.shutdown()
        print("============================================================")

if __name__ == '__main__':
    run_simulation()
