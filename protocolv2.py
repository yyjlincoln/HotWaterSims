import struct
import socket
import time
import json
import random
from functools import wraps
import secrets
import logging

logging.basicConfig(level=logging.DEBUG)


class Events():
    def __init__(self, client_id):
        super().__init__()
        self.client_id = client_id
        self.struct_format = '16s16s16sf'
        self.event_callbacks = {}

    def make(self, event, body, ref=None):
        if not isinstance(body, dict):
            raise TypeError(
                'Body must be a dictionary so it can be encoded to json format!')
        head = struct.pack(self.struct_format, self.client_id.encode('utf-8'),
                           secrets.token_hex(16).encode('utf-8') if not ref else ref.encode('utf-8'), event.encode('utf-8'), time.time())
        # Try to encode body
        try:
            body = json.dumps(body).encode('utf-8')
        except json.JSONDecodeError as e:
            raise TypeError('Body must be able to converted to json format!')
        return b'$!$!'+head+body+b'!$!$'

    def load(self, binary, disable_client_id_check=False):
        # Check flag
        if binary[:4]!=b'$!$!' or binary[-4:]!=b'!$!$':
            logging.warning('Invalid flag, the message should start with $!$! and end with !$!$. Discard message.')
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
            logging.info('Failed to unpack head due to struct error.', e)
            return None, None

        if client_id != self.client_id and not disable_client_id_check:
            logging.warning('Client_id mismatch. Discard message.')
            return None, None

        # Try to load body
        try:
            body = json.loads(body)
        except json.JSONDecodeError as e:
            logging.warning('Could not decode body. Discard message.', e)
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
            def _on_specific_event(*, ref=None, _do_not_directly_call=True):
                if not ref or _do_not_directly_call:
                    raise RuntimeError(
                        '''Event handlers must not be called directly. If this is not called directly, then ref is missing.''')

                @wraps(func)
                def _process_request(*args, **kw):
                    res = func(*args, **kw)
                    return self.make('response', res, ref=ref)
                return _process_request

            if event in self.event_callbacks:
                self.event_callbacks[event].append(_on_specific_event)
                # Instead of using func which is not handled by the decorator, _on_specific_event is used so that it can be handled by the decorator.
            else:
                self.event_callbacks[event] = [_on_specific_event]

            return _on_specific_event
        return _initialize_on
    
    def listen(self, open_connection):
        while True:
            pool = open_connection.recv(2048)
            expect = b'$!$!' # This gets toggled every time something is detected.
            buffer = b''
            # 循环获取pool，与buffer的后3位一起使用kmp算法匹配expect（防止标志符被切断）（并循环调用kmp，切换标志符号，直到无法找到匹配为止，返回列表）。如果匹配成功则将pool中匹配到的部分与buffer一同callback，然后将剩余pool部分加入buffer；否则增加内容进buffer，进入下一轮循环。
            # 在发送端设置queue发送；中间不需要有间隔。

            # Test
            if 'test' in self.event_callbacks:
                for callback in self.event_callbacks['test']:
                    print(callback(ref='testref',_do_not_directly_call=False)('TestArgument'))



t = Events('testID')

@t.on('test')
def test(Tst):
    print(Tst)
    return {
        'c':'ok'
    }

t.listen('1')