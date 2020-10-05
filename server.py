from protocolv2 import Events
import threading
import socket

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
s.bind(('localhost',8080))
s.listen(10)


def connectionMonitor(openconn):
    print('start')
    ctx = Events(server_mode=True)

    @ctx.on('echo')
    def echo(head, body):
        print('echoservice')
        return {
            'code': 0,
            'message':'Your client id is: ' + head['client_id'],
            'payload':body,
            'ref':head['ref']
        }

    ctx.listen(openconn)
    

while True:
    openconn, addr = s.accept()
    t = threading.Thread(target=connectionMonitor, args=(openconn,))
    t.setDaemon(True)
    t.start()