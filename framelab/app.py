"""Application lifecycle and one-click browser launch."""
import argparse
import json
import logging
import sys
import webbrowser
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from .api.http import handler
from .config import data_dir
from .services.session import Service


def running_url(port):
    connection = HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        connection.request("GET", "/api/health")
        response = connection.getresponse()
        if response.status == 200 and json.loads(response.read()).get("app") == "frame-lab":
            return f"http://127.0.0.1:{port}"
    except (OSError, ValueError):
        pass
    finally:
        connection.close()
    return None


def main():
    parser = argparse.ArgumentParser(description="Frame Lab local web app")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    folder = data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=folder / "app.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    service = Service()
    server = None
    for port in range(args.port, min(args.port + 10, 65536)):
        url = running_url(port)
        if url:
            if not args.no_browser:
                webbrowser.open(url)
            if sys.stdout:
                print("Frame Lab is already running: " + url, flush=True)
            return
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler(service))
            break
        except OSError:
            continue
    if server is None:
        raise RuntimeError("Không tìm được cổng cục bộ. Kiểm tra app.log.")
    url = f"http://127.0.0.1:{server.server_port}"
    logging.info("Started at %s", url)
    if sys.stdout:
        print("Frame Lab: " + url, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logging.info("Stopped")


if __name__ == "__main__":
    main()
