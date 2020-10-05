import struct
import socket
import time
import json
import random
from functools import wraps
import secrets
import logging
import kmp

logging.basicConfig(level=logging.DEBUG)


class Events():
    def __init__(self, client_id):
        self.client_id = client_id
        self.struct_format = '16s16s16sf'
        self.event_callbacks = {}
        self.server_mode = False
        super().__init__()

    def make(self, event, body, ref=None, client_id=None):
        if self.server_mode and not client_id:
            raise Exception('On server mode, client_id must be supplied.')
        if not isinstance(body, dict):
            raise TypeError(
                'Body must be a dictionary so it can be encoded to json format!')

        head = struct.pack(self.struct_format, self.client_id.encode('utf-8') if not client_id else client_id.encode('utf-8'),
                           secrets.token_hex(16).encode('utf-8') if not ref else ref.encode('utf-8'), event.encode('utf-8'), time.time())
        # Try to encode body
        try:
            body = json.dumps(body).encode('utf-8')
        except json.JSONDecodeError as e:
            raise TypeError('Body must be able to converted to json format!')
        return b'$$$$'+head+body+b'!!!!'

    def load(self, binary):
        # Check flag
        if binary[:4] != b'$$$$' or binary[-4:] != b'!!!!':
            logging.warning(
                'Invalid flag, the message should start with $$$$ and end with !!!!. Discard message.')
            return None, None
        binary = binary[4:-4]
        head, body = binary[:struct.calcsize(
            self.struct_format)], binary[struct.calcsize(self.struct_format):]
        try:
            client_id, ref, ev, ts = struct.unpack(self.struct_format, head)
            client_id = client_id.decode('utf-8').split('\0', 1)[0]
            # Removes null characters as well
            ref = ref.decode('utf-8').split('\0', 1)[0]
            ev = ev.decode('utf-8').split('\0', 1)[0]
        except struct.error as e:
            logging.info('Failed to unpack head due to struct error. ' + str(e))
            return None, None

        if client_id != self.client_id and not self.server_mode:
            logging.warning('Client_id mismatch. Discard message.')
            return None, None

        # Try to load body
        try:
            body = json.loads(body)
        except json.JSONDecodeError as e:
            logging.warning('Could not decode body. Discard message.'+ str(e))
            return None, None

        return {
            'client_id': client_id,
            'ref': ref,
            'ev': ev,
            'ts': ts
        }, body

    def on(self, event):
        def _initialize_on(func):

            @wraps(func)
            def _on_specific_event(*, head, _do_not_directly_call=True):
                if not head or _do_not_directly_call:
                    raise RuntimeError(
                        '''Event handlers must not be called directly. If this is not called directly, then ref is missing.''')

                @wraps(func)
                def _process_request(*args, **kw):
                    res = func(*args, **kw)
                    return self.make('response', res, ref=head['ref'], client_id=head['client_id'])
                return _process_request

            if event in self.event_callbacks:
                self.event_callbacks[event].append(_on_specific_event)
                # Instead of using func which is not handled by the decorator, _on_specific_event is used so that it can be handled by the decorator.
            else:
                self.event_callbacks[event] = [_on_specific_event]

            return _on_specific_event
        return _initialize_on

    def listen(self, open_connection):
        # This gets toggled every time something is detected.
        expect_head = True
        buffer = b''
        while True:
            try:
                newcont = open_connection.recv(2048)
                buffer += newcont
            except:
                raise Exception('Socket disconnected')

            logging.debug('Buffer ' + str(buffer))
            s = kmp.kmp_search(b'$$$$' if expect_head else b'!!!!', buffer)
            while s != -1:
                # Tag detected.
                if not expect_head:  # It was an end tag
                    logging.debug('End tag at ' + str(s))
                    logging.debug(buffer[:s+4])
                    logging.debug('Above content')
                    try:
                        head, body = self.load(buffer[:s+4])
                        if head and body:
                            if head['ev'] in self.event_callbacks:
                                for callback in self.event_callbacks[head['ev']]:
                                    callback(head = head, _do_not_directly_call = False)(head, body)
                        else:
                            logging.warning('Unable to parse the request!')
                    except Exception as e:
                        logging.exception(e)
                        raise


                    # Only preserve buffer after the end flag. i.e. Delete unused / unmatched buffer
                    # as they will no longer be matched correctly. for example, ab$$$$cde!!!!fg --> buffer = fg.
                    buffer = buffer[s+4:]
                else:
                    logging.debug('Start tag at ' + str(s))
                    # Clear buffer before
                    buffer = buffer[s:]

                expect_head = not expect_head  # Reverse the expect, find the end tag

                s = kmp.kmp_search(b'$$$$' if expect_head else b'!!!!', buffer)

            # There is no match
            if newcont == b'':
                # Socket is disconnected
                raise Exception('Socket is disconnected')


t = Events('testID')


@t.on('test')
def test(head, body):
    logging.debug(head, body)
    print(body)
    return {
        'c': 'ok'
    }

print(t.make('test',{
    'test':True
}))

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 8080))
s.listen(10)
con, addr = s.accept()
logging.debug('Started')
t.listen(con)
