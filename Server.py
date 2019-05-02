from threading import Thread
from socket import AF_INET, socket, SOCK_STREAM


clients = {}
addresses = {}
aux_clients = {}

HOST = 'localhost'
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

continue_listening = True


def accept_incoming_connections():
    """Funcion para manejar la conexion de nuevos clientes"""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s Se ha conectado." % client_address)
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()


def handle_client(client):
    """Funcion para manejar a los clientes"""

    name = client.recv(BUFSIZ).decode("utf8")
    clients[client] = name
    # No repetir nombres de clientes
    aux_clients[name] = client
    print(name)
    msg = "serverupdt|%s Se ha unido!" % name
    msg_user_list = str(list(clients.values()))
    msg = msg+" listado de usuarios: "+msg_user_list
    broadcast(bytes(msg, "utf8"))
    global continue_listening
    while continue_listening:
        msg = client.recv(BUFSIZ)
        print(msg)
        decoded_msg = msg.decode("utf-8").split('|')
        print(decoded_msg)
        if decoded_msg[0] == "file":
            print("file")
            continue_listening = False
            broadcast(bytes(decoded_msg[1]+"|"+name+"|"
                            + "File Sent: "+decoded_msg[2], "utf-8"))
            send_file_to_client(client, decoded_msg[1], decoded_msg[2])
        elif decoded_msg[0] != "{quit}":
            if decoded_msg[0] == "broadcast":
                broadcast(msg)
            else:
                send_message_to_clients(msg)
        else:
            client.close()
            del clients[client]
            del aux_clients[name]
            msg = "serverupdt|%s Se ha ido, ista de clientes." % name
            msg_user_list = str(list(clients.values()))
            msg = msg+" listado de usuarios: "+msg_user_list
            broadcast(bytes(msg, "utf8"))
            break


def send_message_to_clients(message):
    message = message.decode("utf8").split("|")
    userlist = message[:-2]
    print(userlist)
    for client in userlist:
        if client in aux_clients:
            client_to = aux_clients[client]
            msg = client+"|" + message[-2]+"|"+message[-1]
            print(msg)
            client_to.send(bytes(msg, "utf-8"))


def send_file_to_client(current, _client, file_name_format):
    file_name_format = file_name_format.split('.')
    f_format = file_name_format.pop()
    f_name = ' '.join(file_name_format)
    filename_l = 'temp.'+f_format
    current.settimeout(1)
    with open(filename_l, 'wb') as f:
        print('file opened')
        while True:
            print('receiving data...')
            try:
                data = current.recv(BUFSIZ)
                print('data=%s' % data)
                f.write(data)
            except OSError:
                print('done...')
                break

    # TODO send waring for file return

    print("forwarding to client")
    client_to = aux_clients[_client]
    client_to.send(bytes("file|"+f_name+"."+f_format, "utf-8"))

    f = open(filename_l, 'rb')
    chunk = f.read(BUFSIZ)
    while (chunk):
        client_to.send(chunk)
        print('Sent ', repr(chunk))
        chunk = f.read(BUFSIZ)
    f.close()
    client_to.send(bytes("stop", "utf-8"))
    print('Done sending')
    current.settimeout(None)
    global continue_listening
    continue_listening = True


def broadcast(msg, prefix=""):  # prefix para identificacion de nombre
    """Envia un mensaje hacia todos los clientes"""

    for sock in clients:
        sock.send(bytes(prefix, "utf8")+msg)


if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
