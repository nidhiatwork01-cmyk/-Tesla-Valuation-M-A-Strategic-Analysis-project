"""
WSGI Application entrypoint for Vercel deployment.
Serves the Tesla Valuation & M&A Strategic Analysis executive presentation and deliverables.
Zero external dependencies required (uses standard Python library).
"""
import os
import mimetypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def app(environ, start_response):
    path = environ.get("PATH_INFO", "/").lstrip("/")
    
    if not path or path == "":
        target = os.path.join(BASE_DIR, "index.html")
    else:
        # Prevent directory traversal
        safe_path = os.path.normpath(path)
        if safe_path.startswith(".."):
            start_response("403 Forbidden", [("Content-Type", "text/plain")])
            return [b"Forbidden"]
        target = os.path.join(BASE_DIR, safe_path)

    if os.path.isfile(target):
        mime, _ = mimetypes.guess_type(target)
        mime = mime or "application/octet-stream"
        with open(target, "rb") as f:
            content = f.read()
        start_response("200 OK", [
            ("Content-Type", mime),
            ("Content-Length", str(len(content))),
        ])
        return [content]

    # Fallback to index.html
    fallback = os.path.join(BASE_DIR, "index.html")
    if os.path.isfile(fallback):
        with open(fallback, "rb") as f:
            content = f.read()
        start_response("200 OK", [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(content))),
        ])
        return [content]

    start_response("404 Not Found", [("Content-Type", "text/plain")])
    return [b"Not Found"]
