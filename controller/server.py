import socket

s = socket.socket()
print("Create Socket")

port = 6969

s.bind(('', port))

s.listen(5)

while True:
    c, addr = s.accept()
    
    print("got connection from:", addr)
    
    c.send("Thank you for connecting".encode())

    c.close()