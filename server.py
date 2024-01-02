#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import host
import guests
import re
import sys

class APIServer(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def _serve_content(self, filepath, content_type="text/html"):
        try:
            with open(filepath, "rb") as file:
                content = file.read()
                self._set_headers(content_type=content_type)
                self.wfile.write(content)
        except FileNotFoundError:
            self._set_headers(status_code=404, content_type="text/plain")
            self.wfile.write(bytes("File not found.", "utf-8"))

    def serve_favicon(self):
        self._serve_content(filepath="resources/favicon.ico", content_type="image/x-icon")

    def serve_landing(self):
        self._serve_content(filepath="pages/landing.html")

    def describe_api(self):
        self._serve_content(filepath="pages/api.html")

    def describe_apiv1(self):
        self._serve_content(filepath="pages/apiv1.html")

    def describe_host(self):
        response_data = json.dumps(host.describe_host(), indent=4)
        self._set_headers()
        self.wfile.write(response_data.encode())

    def describe_host_cpu(self):
        response_data = json.dumps({"freeCPU": host.describe_cpu_cores()}, indent=4)
        self._set_headers()
        self.wfile.write(response_data.encode())

    def describe_host_disk(self):
        response_data = json.dumps(host.describe_disk_usage(), indent=4)
        self._set_headers()
        self.wfile.write(response_data.encode())

    def describe_host_memory(self):
        response_data = json.dumps({"freeMemory": host.describe_memory_usage()}, indent=4)
        self._set_headers()
        self.wfile.write(response_data.encode())

    def describe_host_maxvcpu(self):
        response_data = json.dumps({"maxvCPU": host.get_max_vcpu()}, indent=4)
        self._set_headers()
        self.wfile.write(response_data.encode())

    # TODO: Implement `guest` methods

    def describe_guests(self):
        self._set_headers()
        self.wfile.write(bytes("Under construction.", "utf-8"))
        pass

    def describe_guest(self, guest_name):
        self._set_headers()
        self.wfile.write(bytes("Under construction.", "utf-8"))
        pass

    def describe_guest_cpu(self, guest_name):
        self._set_headers()
        self.wfile.write(bytes("Under construction.", "utf-8"))
        pass

    def describe_guest_disk(self, guest_name):
        self._set_headers()
        self.wfile.write(bytes("Under construction.", "utf-8"))
        pass

    def describe_guest_memory(self, guest_name):
        self._set_headers()
        self.wfile.write(bytes("Under construction.", "utf-8"))
        pass

    def do_GET(self):
        routes = {
            "/": self.serve_landing,
            "/favicon.ico": self.serve_favicon,
            "/resources/favicon.ico": self.serve_favicon,
            "/api": self.describe_api,
            "/api/v1": self.describe_apiv1,
            "/api/v1/host": self.describe_host,
            "/api/v1/host/cpu": self.describe_host_cpu,
            "/api/v1/host/disk": self.describe_host_disk,
            "/api/v1/host/memory": self.describe_host_memory,
            "/api/v1/host/maxvcpu": self.describe_host_maxvcpu,
            "/api/v1/guests": self.describe_guests,
            "/api/v1/guests/([^/]+)": self.describe_guest,
            "/api/v1/guests/([^/]+)/cpu": self.describe_guest_cpu,
            "/api/v1/guests/([^/]+)/disk": self.describe_guest_disk,
            "/api/v1/guests/([^/]+)/memory": self.describe_guest_memory
        }

        if self.path.startswith("/api/v1/guests/"):
            for path,handler in routes.items():
                match = re.match(f"^{path}$", self.path)
                if match:
                    guest_name = match.groups()[0]
                    handler(guest_name)
        elif self.path in routes.keys():
            routes[self.path]()
        else:
            self._set_headers(status_code=404, content_type="text/plain")
            self.wfile.write(bytes("Resource not found.", "utf-8"))

    # TODO: Implement `POST`, `DELETE`, and `UPDATE`/`PATCH` methods
    def do_POST(self):
        if self.path == "/api/v1/guests/":
            content_length = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_length).decode('utf-8')

            try:
                params = json.loads(post_body)
                guests.create_guest(name=params["name"], cpu=params["cpu"], memory=params["memory"], disk_size=params["diskSize"], network=params["network"], os_version=params["osVersion"], disk_image=params["diskImage"], host_name=params["hostName"], pdomain_name=params["domainName"], full_name=params["fullName"], username=params["username"])
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(bytes(f"Creation of VM {params['name']} in progress...", "utf-8"))
            except json.JSONDecodeError:
                self._set_headers(400, 'text/plain')
                self.wfile.write("Invalid JSON".encode())
                return
            
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("Invalid request path.", "utf-8"))

    def do_DELETE(self):
        if self.path.startswith("/api/v1/guests/"):
            self.send_response(200)
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("Invalid request path.", "utf-8"))

def help():
    # TODO: Create `help()` message
    return ""

def read_args(args):
    server_args = ["localhost", 8080]

    if len(sys.argv) == 1:
        return server_args
    elif (len(sys.argv) % 2 == 0) or (len(sys.argv) > 5):
        raise ValueError(f"Invalid number of arguments.\n{help()}")

    while len(args) > 1:
        option = args.pop(1)
        arg = args.pop(1)
        if (option == "--hostname") or (option == "-h"):
            if type(arg) is not str:
                raise ValueError(f"Invalid hostname.\n{help()}") 
            server_args[0] = arg
        elif (option == "--port") or (option == "-p"):
            try:
                arg = int(arg)
            except ValueError:
                print(f"ValueError: Invalid port number: Must be an integer.", file=sys.stderr)
                sys.exit(1)
            if (arg < 0) or (arg > 65535):
                raise ValueError(f"Invalid port number: Must be in range 0-65535.\n{help()}")
            server_args[1] = arg

    return server_args


def run_server(hostname="localhost", port=8080):
    api_server = HTTPServer((hostname, port), APIServer)
    print("virt-agent started on http://%s:%s" % (hostname, port))

    try:
        api_server.serve_forever()
    except KeyboardInterrupt:
        pass
    
    api_server.server_close()
    print("virt-agent stopped.")


def main():
    hostname, port = read_args(sys.argv)
    run_server(hostname, port)

if __name__ == "__main__":
    main()
