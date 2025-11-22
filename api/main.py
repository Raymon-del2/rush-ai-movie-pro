from app import app
import json

def handler(event, context):
    # Vercel serverless function handler
    try:
        # Convert Vercel event to WSGI environ
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        query = event.get('queryStringParameters', {}) or {}
        body = event.get('body', '')
        
        # Create WSGI environ
        environ = {
            'REQUEST_METHOD': method,
            'PATH_INFO': path,
            'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in query.items()]),
            'CONTENT_TYPE': headers.get('content-type', ''),
            'CONTENT_LENGTH': str(len(body)) if body else '0',
            'SERVER_NAME': 'vercel.app',
            'SERVER_PORT': '443',
            'wsgi.url_scheme': 'https',
            'wsgi.input': body,
            'wsgi.errors': None,
            'wsgi.version': (1, 0),
            'wsgi.multithread': False,
            'wsgi.multiprocess': False,
            'wsgi.run_once': False,
        }
        
        # Add headers to environ
        for key, value in headers.items():
            environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
        
        # Start response
        response_data = {}
        def start_response(status, response_headers):
            response_data['status'] = status
            response_data['headers'] = response_headers
        
        # Call app
        result = app(environ, start_response)
        response_body = ''.join(result)
        
        return {
            'statusCode': int(response_data['status'].split()[0]),
            'headers': dict(response_data['headers']),
            'body': response_body
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }
