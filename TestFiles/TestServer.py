
import socket                   # Import socket module


port = 50000
s = socket.socket()             # Create a socket object
host = "localhost"   # Get local machine name
s.bind((host, port))            # Bind to the port
s.listen(5)                     # Now wait for client connection.

print('Server listening....')


while True:
    conn, addr = s.accept()     # Establish connection with client.
    print('Got connection from', addr)
    data = conn.recv(1024)
    print('Server received', repr(data))

    filename = 'image.jpeg'
    f = open(filename, 'rb')
    chunk = f.read(1024)
    while (chunk):
        conn.send(chunk)
        print('Sent ', repr(chunk))
        chunk = f.read(1024)
    f.close()

    print('Done sending')
    conn.send(bytes('Thank you for connecting', "utf-8"))
    conn.close()
