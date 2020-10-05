from protocolv2 import Events
import socket

s = socket.socket()
s.connect(('localhost',8080))

ctx = Events('TestClientA')

ctx.emit('echo',{
    'payload!':'stuff'
}, s).then(print)

@ctx.response()
def res(head, body):
    print(body)

ctx.listen(s)