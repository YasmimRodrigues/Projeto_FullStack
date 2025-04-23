from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import json
import uvicorn
from fastapi import FastAPI
from fastapi.applications import AppType
from fastapi.responses import Response
from app import create_app
from app.utils.logger import setup_logging, logger

# Set up logging
setup_logging()

# Create FastAPI application
asgi_app = create_app()

# Create a Flask-like WSGI app that can be used by gunicorn
class WSGIApp:
    def __init__(self, app: AppType) -> None:
        self.app = app
        
    async def _run_asgi_app(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> None:
        await self.app(scope, receive, send)
    
    def __call__(self, environ: Dict[str, Any], start_response: Callable) -> List[bytes]:
        # Convert WSGI environ to ASGI scope
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.1").split("/")[1],
            "method": environ.get("REQUEST_METHOD", "GET"),
            "scheme": environ.get("wsgi.url_scheme", "http"),
            "path": environ.get("PATH_INFO", "/"),
            "raw_path": environ.get("PATH_INFO", "/").encode(),
            "query_string": environ.get("QUERY_STRING", "").encode(),
            "root_path": environ.get("SCRIPT_NAME", ""),
            "client": (environ.get("REMOTE_ADDR", ""), int(environ.get("REMOTE_PORT", 0))),
            "server": (environ.get("SERVER_NAME", ""), int(environ.get("SERVER_PORT", 0))),
        }
        
        # Process headers
        headers = []
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                header_name = key[5:].lower().replace('_', '-').encode()
                header_value = value.encode()
                headers.append((header_name, header_value))
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                header_name = key.lower().replace('_', '-').encode()
                header_value = value.encode()
                headers.append((header_name, header_value))
                
        # Special handling for Authorization header
        if 'HTTP_AUTHORIZATION' in environ:
            auth_value = environ['HTTP_AUTHORIZATION'].encode()
            headers.append((b'authorization', auth_value))
            
        scope['headers'] = headers

        # Simple WSGI response handling
        body = []
        status_code = [200]
        headers = [None]
        
        # Define ASGI send function
        async def send(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
                headers[0] = [(k.decode(), v.decode()) for k, v in message.get("headers", [])]
            elif message["type"] == "http.response.body":
                body.append(message.get("body", b""))
        
        # Define ASGI receive function
        async def receive() -> Dict[str, Any]:
            # Simple implementation for a request
            content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
            body = environ.get("wsgi.input").read(content_length) if content_length > 0 else b""
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }
        
        # Run the ASGI app
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._run_asgi_app(scope, receive, send))
        
        # Send response to WSGI
        status = f"{status_code[0]} OK"
        start_response(status, headers[0] or [])
        return body

# Create a WSGI-compatible wrapper for our FastAPI app
app = WSGIApp(asgi_app)

if __name__ == "__main__":
    # Run the application with uvicorn directly (for development)
    uvicorn.run(asgi_app, host="0.0.0.0", port=5000, reload=True)
