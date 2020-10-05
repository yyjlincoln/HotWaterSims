from protocolv2 import Events
import socket

s = socket.socket()
s.connect(('localhost',8080))

ctx = Events('TestClientA')

ctx.emit('echo',{
    'payload!':'stuff'
}, s)

@ctx.on('response')
def res(head, body):
    print(body)
    return {
        'code':'ok'
    }

ctx.listen(s)