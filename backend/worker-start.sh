#!/usr/bin/env bash
set -o errexit

python manage.py migrate

celery -A uptracker beat --loglevel=info &
celery -A uptracker worker --loglevel=info -P solo &

python -c "
import http.server, socketserver, os
PORT = int(os.environ.get('PORT', 8000))
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'worker alive')
    def log_message(self, format, *args):
        pass
with socketserver.TCPServer(('', PORT), Handler) as httpd:
    httpd.serve_forever()
"