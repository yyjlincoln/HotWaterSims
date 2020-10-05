from protocolv2 import Events
import socket

max_trial = 5
trial = 0

while True:
    try:
        s = socket.socket()
        s.connect(('localhost', 8080))

        ctx = Events('TestClientA')

        ctx.emit('echo', {
            'payload!': 'stuff'
        }, s).then(print)

        @ctx.response()
        def res(head, body):
            print(body)
    
        ctx.listen(s)
        # This will block all requests until an exception is thrown
    except Exception as e:
        print(e)
        trial += 1
        if trial == max_trial:
            break
        continue
