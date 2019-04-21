import tkinter
from tkinter import messagebox, filedialog
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
from Crypto import Crypto as cr

# Variables de configuración para el server

SERVER = "localhost"
PORT = 33000
BUFSIZE = 1024
ADDR = (SERVER, PORT)

# Variables de configuracion para  el cliente

client_socket = socket(AF_INET, SOCK_STREAM)

# Contenedor y variables globales para la interfaz
top = tkinter.Tk()
top.title("Interfaz de manejo de clientes")
com_window = ""
new_client_name = tkinter.StringVar()
my_client_name = tkinter.StringVar()
password = tkinter.StringVar()
my_msg = tkinter.StringVar()
connect_server_button = ""
connect_client_button = ""
# Nombres para la comunicacion
client_from = ""
my_name = ""
# Listas para mensajes y usuarios
msg_list = ""
users_list = ""
key = ""
# Variables globales para el envio y conexion
continue_receiving = True
client_connected = None
is_broadcast = None
is_secure = None


def receive():
    """Funcion que maneja los mensajes recividos"""
    global client_from
    global continue_receiving
    while continue_receiving:
        try:
            msg = client_socket.recv(BUFSIZE).decode("utf8")
            msg_decoded = msg.split('|')
            print(msg_decoded)
            # comprobar si es el usuario indicado
            if msg_decoded[0] == my_name:
                # comprobar si es necesario desencriptar el mensaje
                if is_secure is None:
                    msg_list.insert(tkinter.END, msg_decoded[1]+": " +
                                    msg_decoded[2])
                else:
                    msg = cr.decrypt(
                        bytes(msg_decoded[2], "utf-8"), key).decode("utf-8")
                    msg_list.insert(tkinter.END, msg_decoded[1]+": " +
                                    msg)
            # comprobar si es que es un mensaje de broadcast
            elif msg_decoded[0] == "broadcast" and msg_decoded[1] != my_name:
                msg_list.insert(
                    tkinter.END, "Mensaje Broadcast de: "
                    + msg_decoded[1]+": "+msg_decoded[2])
            # comprobar si es que es un mensaje del server

            elif msg_decoded[0] == "file":
                client_socket.settimeout(2)
                with open(msg_decoded[1], 'wb') as f:
                    print('file opened')
                    while True:
                        print('receiving data...')
                        try:
                            data = client_socket.recv(BUFSIZE)
                            print('data=%s' % data)
                            f.write(data)
                        except OSError:
                            print('done receiving data from client...')
                            break
                client_socket.settimeout(None)
            elif msg_decoded[0] == "serverupdt":
                users_list.insert(tkinter.END, msg_decoded[1])
        except OSError:  # Manejo de excepciones.
            break

            # TODO make condition to accept files


def on_closing(event=None):
    """Funcion para el cierre de la ventana de comunicacion"""
    global continue_receiving, connect_client_button, connect_server_button
    connect_client_button.config(state="normal")
    connect_server_button.config(state="normal")
    my_msg.set("{quit}")
    send()
    print("Comunicacion parada")
    continue_receiving = False


def send(event=None):
    """Esta funcion se encarga del envio de los mensajes"""
    msg = my_msg.get()
    my_msg.set("")
    if msg == "{quit}":
        # para cerrar la comunicacion
        client_socket.send(bytes(msg, "utf8"))
        client_socket.close()
        com_window.destroy()
    elif is_broadcast is True:
        # Comprobar si enviamos un mensaje de broadcast
        client_socket.send(bytes("broadcast|"+my_name+"|"+msg, "utf8"))
        msg_list.insert(tkinter.END, my_name+" Broadcast: "+msg)
    elif is_secure is True:
        # comprobamos si enviamos un mensaje encriptado
        msg_list.insert(tkinter.END, my_name+": "+msg)
        msg = cr.encrypt(msg, key).decode("utf-8")
        client_socket.send(bytes(client_from+"|"+my_name+"|"+msg, "utf8"))
    # enviamos un mensaje normal
    else:
        client_socket.send(bytes(client_from+"|"+my_name+"|"+msg, "utf8"))
        msg_list.insert(tkinter.END, my_name+": "+msg)


def send_file():
    top.filename = filedialog.askopenfilename(
        initialdir="/", title="Select file",
        filetypes=(("jpeg files", "*.jpg"),
                   ("all files", "*.*")))
    file_name = top.filename
    print(file_name)
    f = open(file_name, 'rb')
    chunk = f.read(1024)
    client_socket.send(bytes("file|"+client_from+"|" +
                             file_name.split('/')[-1], "utf8"))
    while (chunk):
        client_socket.send(chunk)
        print('Sent ', repr(chunk))
        chunk = f.read(1024)
    f.close()
    print("done sending to server")


def create_comunication_gui(client_name, client_to):
    """Función para crear la interfaz secundaria de comunicación
    """
    global client_from, my_name, com_window, msg_list
    my_name = client_name
    print(client_name + " a "+client_to)
    client_from = client_to
    com_window = tkinter.Toplevel(top)
    com_window.title(client_name + " a "+client_to)
    messages_frame = tkinter.Frame(com_window)
    my_msg.set("Escribe tu mensaje aqui")
    scrollbar = tkinter.Scrollbar(messages_frame)
    scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    msg_list = tkinter.Listbox(messages_frame, height=15,
                               width=50, yscrollcommand=scrollbar.set)
    msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
    msg_list.pack()
    messages_frame.pack()
    entry_field = tkinter.Entry(com_window, textvariable=my_msg)
    entry_field.bind("<Return>", send)
    entry_field.pack()
    send_button = tkinter.Button(com_window, text="Enviar", command=send)
    send_button.pack()
    send_file_button = tkinter.Button(
        com_window, text="Enviar Archivo", command=send_file)
    send_file_button.pack()
    com_window.protocol("WM_DELETE_WINDOW", on_closing)


def connect_server():
    """Conectar con el servidor, validando que la conexion sea posible
    """
    if my_client_name.get() != "":
        global continue_receiving
        global client_socket
        if continue_receiving is False:
            client_socket = socket(AF_INET, SOCK_STREAM)
            continue_receiving = True
        client_socket.connect(ADDR)
        receive_thread = Thread(target=receive)
        receive_thread.start()
        client_socket.send(bytes(my_client_name.get(), "utf8"))
        global client_connected, connect_server_button
        client_connected = True
        connect_server_button.config(state="disabled")


def connect_client():
    """Conectar con el cliente, validando las entradas
    """
    if my_client_name.get() == "" or new_client_name.get() == "":
        messagebox.showerror(
            "Error Al Abrir chat",
            "No se ha especificado el destinatario y el usuario")
    elif client_connected is True:
        global connect_client_button
        connect_client_button.config(state="disabled")
        create_comunication_gui(my_client_name.get(), new_client_name.get())
    else:
        messagebox.showerror(
            "Error Al Abrir chat", "No se ha conectado el cliente al servidor")


def configure_broadcast():
    """Funcion para habilitar mensajes broadcast
    """
    global is_broadcast
    if is_broadcast is None:
        is_broadcast = True
        messagebox.showinfo("Configuracion", "Modo Chat Room Activado")
    else:
        is_broadcast = None
        messagebox.showinfo("Configuracion", "Modo Chat Room Desactivado")


def configure_secure_layer():
    """Funcion para habilitar un canal seguro
    """
    global is_secure, key
    if is_secure is None:

        if password.get() != "":
            key = cr.generate_key(password.get())
            is_secure = True
            messagebox.showinfo("Configuracion", "Modo Seguro Activado")
        else:
            messagebox.showinfo("Error", "Ingrese un password")
    else:
        is_secure = None
        messagebox.showinfo("Configuracion", "Modo Seguro Desactivado")


# Crear la interfaz principal

users_frame = tkinter.Frame(top)
scroll_bar = tkinter.Scrollbar(users_frame)
users_list = tkinter.Listbox(
    users_frame, height=20, width=75,
    yscrollcommand=scroll_bar.set)
scroll_bar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
users_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
users_list.pack()
users_frame.pack()

lbl_client = tkinter.Label(top, text="Nombre del cliente")
lbl_client.pack(side="left")
entry_field = tkinter.Entry(top, textvariable=my_client_name)
entry_field.bind("<Return>", connect_client)
entry_field.pack(side="left")

lbl_client_to = tkinter.Label(top, text="Nombre del destinatario")
lbl_client_to.pack(side="left")
entry_field = tkinter.Entry(top, textvariable=new_client_name)
entry_field.bind("<Return>", connect_client)
entry_field.pack(side="left")

lbl_pwd = tkinter.Label(top, text="Contraseña")
lbl_pwd.pack(side="left")

entry_field = tkinter.Entry(top, textvariable=password)
entry_field.pack(side="left")

connect_server_button = tkinter.Button(
    top, text="Conectar Servidor", command=connect_server)
connect_server_button.pack()
connect_client_button = tkinter.Button(
    top, text="Conectar Cliente", command=connect_client)
connect_client_button.pack()

broadcast_button = tkinter.Button(
    top, text="Chat Room", command=configure_broadcast)
broadcast_button.pack()

secure_button = tkinter.Button(
    top, text="Seguro", command=configure_secure_layer)
secure_button.pack()

# Corremos la interfaz principal
tkinter.mainloop()
