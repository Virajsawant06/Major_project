import email
from io import StringIO
import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parse_raw_request(raw_text):
    """
    Parses a raw HTTP request string (e.g. from Burp or ZAP) into components.
    Returns: method (str), path (str), headers (dict), body (str)
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Empty request provided.")
        
    # Split headers from body (accepts both \n\n and \r\n\r\n)
    parts = raw_text.split('\r\n\r\n', 1)
    if len(parts) == 1:
        parts = raw_text.split('\n\n', 1)
        
    head_part = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    
    # Parse request line
    lines = head_part.splitlines()
    if not lines:
        raise ValueError("Invalid request format.")
        
    req_line = lines[0].strip().split(' ')
    if len(req_line) < 2:
        raise ValueError("Invalid HTTP request line (e.g., 'POST /api HTTP/1.1').")
        
    method = req_line[0]
    path = req_line[1]
    
    # Parse headers using standard email parser which handles HTTP headers perfectly
    header_string = '\r\n'.join(lines[1:])
    msg = email.message_from_file(StringIO(header_string))
    headers = dict(msg.items())
    
    return method, path, headers, body

def get_full_url(target_url, parsed_path):
    """
    Safely joins the user-provided target_url and the path extracted from the request.
    """
    if parsed_path.startswith("http://") or parsed_path.startswith("https://"):
        return parsed_path
        
    base = target_url.rstrip("/")
    if not parsed_path.startswith("/"):
        parsed_path = "/" + parsed_path
        
    return base + parsed_path

def replay_request(method, url, headers, body, session=None):
    """
    Sends the request exactly as formed.
    """
    if session is None:
        session = requests.Session()
    
    # Clean up conflicting headers from typical captures
    cleaned_headers = dict(headers)
    if 'Content-Length' in cleaned_headers:
        # Python requests will calculate this natively for the tampered body
        del cleaned_headers['Content-Length']
    if 'Accept-Encoding' in cleaned_headers:
        # Allow requests to handle decoding
        del cleaned_headers['Accept-Encoding']
        
    req = requests.Request(method, url, headers=cleaned_headers, data=body)
    prepared = req.prepare()
    
    return session.send(prepared, verify=False, timeout=10)
