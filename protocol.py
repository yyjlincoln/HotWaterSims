import struct
import socket
import time
import json
import random
from functools import wraps


class Protocol:
    def __init__(self, is_server=False, client_id=None, check_client_id=False):
        super().__init__()
        if not is_server and not client_id:
            raise ValueError(
                'A client ID must be supplied when running under the client mode.')
        self.is_server = is_server
        self.client_id = client_id
        self.check_client_id = check_client_id
        self.format = '?i16sQQ16s'
        self.protocol_version = 1

        # Callback functions
        self.events = {}

    class Errors(Exception):
        'All errors related to the protocol.'

    class ParseError(Protocol.Errors):
        # Failed to parse the binary data.
        pass

    class UnrecognizedClientError(Protocol.Errors):
        # The client ID does not match with the current clientID
        pass

    class ReturnTypeError(Protocol.Errors):
        'Return type should be a dictionary'
        pass

    def parse_from_binary(self, bindata: bytes):
        if len(bindata) < struct.calcsize(self.format):
            raise self.ParseError(
                f'Can not parse the data: expecting size of or larger than {str(struct.calcsize(self.format))}, got {len(bindata)}')
        # Now, slice the binary data.
        head = bindata[:struct.calcsize(self.format)]
        # This is stored as json format, so it can be decoded straight away.
        body = bindata[struct.calcsize(self.format):].decode()
        try:
            # Try to parse the head
            request_flag, protocol_version, client_id, timestamp, ref, action = struct.unpack(
                self.format, head)
            # Now, format the data as strings are stored as bytes
            client_id, action = client_id.decode(), action.decode()
        except struct.error:
            raise self.ParseError('Struct error occured.')
        content = {}
        try:
            if body:
                content = json.loads(body)
            else:
                content = {}
        except json.JSONDecodeError:
            raise self.ParseError('JSON Decode error.')
        # Now, validate the client ID
        if not self.is_server:
            if client_id != self.client_id:
                raise self.UnrecognizedClientError('Unrecognized client ID.')

        # Return those for now.
        return request_flag, protocol_version, client_id, timestamp, ref, action, body

    def make_binary(self, request_flag, protocol_version, client_id, timestamp, ref, action, body):
        try:
            return struct.pack(self.format, request_flag, protocol_version, str(client_id).encode(), timestamp, ref, str(action).encode()) + json.dump(body)
        except:
            raise self.ParseError()

    def on(self, event):
        def _on_handler(func):
            if event in self.events:
                self.events[event].append(func)
            else:
                self.events[event] = [func]

            @wraps(func)
            def _on_handler_wrap(*args, ref = None, **kw):
                # Return the response staright away
                res = func(*args, ref = ref, **kw)
                if not isinstance(dict, res):
                    raise self.ReturnTypeError('Return Type must be a dict!')
                return self.make_binary(False, self.protocol_version, self.client_id, int(time.time()), ref, '<Response>')

            return _on_handler_wrap

        return _on_handler


# # Test data
s = struct.pack('?i16sQQ16s', True, 1, b'testclient', int(
    time.time()), random.randint(0, 10000000), b'Test action')
print(len(s))
test = Protocol(is_server=True).parse_from_binary(s)
