#!/usr/bin/env python3
"""
Range-request-capable HTTP server for local portfolio preview.
Python's built-in http.server does not support Range headers,
which breaks video playback in browsers. This server adds Range support.
"""
import http.server
import os
import re
import sys

class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)

        # Let the parent handle directory listings
        if os.path.isdir(path):
            return super().send_head()

        ctype = self.guess_type(path)

        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        fs = os.fstat(f.fileno())
        file_len = fs[6]

        range_header = self.headers.get('Range')
        if range_header:
            m = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if m:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else file_len - 1
                end = min(end, file_len - 1)
                length = end - start + 1

                f.seek(start)
                self.send_response(206, 'Partial Content')
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_len}')
                self.send_header('Content-Length', str(length))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
                self.end_headers()
                return f

        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(file_len))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def log_message(self, fmt, *args):
        # Suppress noisy logs for assets; show main requests
        if not any(args[0].startswith(x) for x in ['GET /thumbs', 'GET /Behind', 'GET /Det']):
            super().log_message(fmt, *args)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3457
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = RangeHTTPRequestHandler
    with http.server.HTTPServer(('', port), handler) as httpd:
        print(f'Portfolio server running at http://localhost:{port}')
        httpd.serve_forever()
