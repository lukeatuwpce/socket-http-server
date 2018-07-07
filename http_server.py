import mimetypes
import os
import socket
import sys

def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    return b'HTTP/1.1 200 OK\r\nContent-Type: ' + mimetype + b'\r\n\r\n' + body


def parse_request(request):
    """
    Given the content of an HTTP request, returns the uri of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.

    Tokenize/parse:

    command uri version
    headers (ignored)

    e.g.:
    GET / HTTP/1.1
    Host: localhost

    Version 1.0 and "connection: close" are not supported/honored.
    """

    received = request.split(" ")
    if len(received) != 3:
        raise NotImplementedError

    command = received.pop(0)
    uri = received.pop(0)
    version = received.pop(0)
    print(f'command {command} uri {uri} version {version}', file=sys.stderr)
    # Remainder unparsed, though 1.1 requries Host.
    # This means we're not closing 1.0 connections or
    # honoring connection: close for 1.1.

    if command != "GET":
        for char in command:
            print(f"{char} : {ord(char)}", file=sys.stderr)
        raise NotImplementedError();
    if not (version == "HTTP/1.1"):
        for char in version:
            print(f"{char} : {ord(char)}", file=sys.stderr)
        raise NotImplementedError();

    return uri


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""
    return b'''HTTP/1.1 405 Method Not Allowed\r\n\r\n'''


def response_not_found():
    """Returns a 404 Not Found response"""
    return b'''HTTP/1.1 404 Not Found\r\n\r\n'''
    

def resolve_uri(uri):
    """
    This method should return appropriate content and a mime type.

    If the requested URI is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the URI is a file, it should return the contents of that file
    and its correct mimetype.

    If the URI does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        resolve_uri('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        resolve_uri('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        resolve_uri('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        resolve_uri('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """

    # TODO: Raise a NameError if the requested content is not present
    # under webroot.

    # TODO: Fill in the appropriate content and mime_type give the URI.
    # See the assignment guidelines for help on "mapping mime-types", though
    # you might need to create a special case for handling make_time.py

    path = 'webroot' + uri

    try:
        with open(path) as fh:
            content = fh.read().encode()
        mime_type = mimetypes.guess_type(path)[0].encode()
    except IsADirectoryError:
        """ The directory listing could be embellished as text/html
        content = ('<html>' + '<br>'.join(os.listdir(path)) + '</html>').encode()
        mime_type = b'text/html'
        """
        content = ('\n'.join(os.listdir(path))).encode()
        mime_type = b'text/plain'
    except FileNotFoundError:
        raise NameError

    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)
                while True:
                    data = conn.recv(4096)
                    print('received "{0}"'.format(data), file=log_buffer)
                    if data:
                        response = ""
                        try:
                            uri = parse_request(data.decode().strip())
                            uri_content, uri_mime = resolve_uri(uri)
                            response = response_ok(uri_content, uri_mime)
                        except NotImplementedError:
                            response = response_method_not_allowed()
                        #except NameError:
                            #response = response_not_found()

                        if response:
                            conn.sendall(response)

                    else:
                        msg = 'no more data from {0}:{1}'.format(*addr)
                        print(msg, log_buffer)
                        break
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return


if __name__ == '__main__':
    server()
    sys.exit(0)


