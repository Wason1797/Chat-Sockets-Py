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

# Variables globales
continue_receiving = True
key = ""
other_client_list = set()


class ControlWindow:
    def __init__(self, _top):
        self.master = _top
        self.master.title("Interfaz de manejo de clientes")
        self.new_client_name = tkinter.StringVar()
        self.my_client_name = tkinter.StringVar()
        self.password = tkinter.StringVar()
        self.users_frame = tkinter.Frame(self.master)
        self.scroll_bar = tkinter.Scrollbar(self.users_frame)
        self.users_list = tkinter.Listbox(
            self.users_frame, height=20, width=75,
            yscrollcommand=self.scroll_bar.set)
        self.scroll_bar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.users_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
        self.users_list.pack()
        self.users_frame.pack()

        self.lbl_client = tkinter.Label(self.master, text="Nombre del cliente")
        self.lbl_client.pack(side="left")
        self.entry_field = tkinter.Entry(
            self.master, textvariable=self.my_client_name)
        self.entry_field.bind("<Return>", self.connect_client)
        self.entry_field.pack(side="left")

        self.lbl_client_to = tkinter.Label(
            self.master, text="Nombre del destinatario")
        self.lbl_client_to.pack(side="left")
        self.entry_field = tkinter.Entry(
            self.master, textvariable=self.new_client_name)
        self.entry_field.bind("<Return>", self.connect_client)
        self.entry_field.pack(side="left")

        self.lbl_pwd = tkinter.Label(self.master, text="Contraseña")
        self.lbl_pwd.pack(side="left")

        self.entry_field = tkinter.Entry(
            self.master, textvariable=self.password)
        self.entry_field.pack(side="left")

        self.connect_server_button = tkinter.Button(
            self.master, text="Conectar Servidor", command=self.connect_server)
        self.connect_server_button.pack()
        self.connect_client_button = tkinter.Button(
            self.master, text="Conectar Cliente", command=self.connect_client)
        self.connect_client_button.config(state="disabled")
        self.connect_client_button.pack()

        self.broadcast_button = tkinter.Button(
            self.master, text="Chat Room", command=self.configure_broadcast)
        self.broadcast_button.pack()

        self.secure_button = tkinter.Button(
            self.master, text="Seguro", command=self.configure_secure_layer)
        self.secure_button.pack()

        self.is_broadcast = None
        self.is_secure = None
        self.is_client_connected = None

        self.child_list = {}

    def connect_server(self):
        """Conectar con el servidor, validando que la conexion sea posible
        """
        if self.my_client_name.get() != "":
            global continue_receiving
            global client_socket
            if continue_receiving is False:
                client_socket = socket(AF_INET, SOCK_STREAM)
                continue_receiving = True
            client_socket.connect(ADDR)
            receive_thread = Thread(target=receive, args=(self,))
            receive_thread.start()
            client_socket.send(bytes(self.my_client_name.get(), "utf8"))

            self.connect_server_button.config(state="disabled")
            self.connect_client_button.config(state="normal")

    def configure_secure_layer(self):
        """Funcion para habilitar un canal seguro
        """
        global key
        if self.is_secure is None:

            if self.password.get() != "":
                key = cr.generate_key(self.password.get())
                self.is_secure = True
                messagebox.showinfo("Configuracion", "Modo Seguro Activado")
            else:
                messagebox.showinfo("Error", "Ingrese un password")
        else:
            self.is_secure = None
            messagebox.showinfo("Configuracion", "Modo Seguro Desactivado")

    def configure_broadcast(self):
        """Funcion para habilitar mensajes broadcast
        """
        if self.is_broadcast is None:
            self.is_broadcast = True
            messagebox.showinfo("Configuracion", "Modo Chat Room Activado")
        else:
            self.is_broadcast = None
            messagebox.showinfo("Configuracion", "Modo Chat Room Desactivado")

    def connect_client(self):
        """Conectar con el cliente, validando las entradas
        """
        if self.my_client_name.get() == "" or self.new_client_name.get() == "":
            messagebox.showerror(
                "Error Al Abrir chat",
                "No se ha especificado el destinatario y el usuario")
        else:
            newWindow = tkinter.Toplevel(self.master)
            newWindow.title(self.my_client_name.get() +
                            " a "+self.new_client_name.get())
            app = ComunicationWindow(
                newWindow, self.my_client_name.get(),
                self.new_client_name.get(), self)
            self.child_list[self.new_client_name.get()] = app
            self.is_client_connected = True


class ComunicationWindow:
    def __init__(self, _top, _my_name, _client_to, _parent):
        self.parent = _parent
        self.my_name = _my_name
        self.client_to = _client_to
        self.master = _top
        self.messages_frame = tkinter.Frame(self.master)
        self.my_msg = tkinter.StringVar()
        self.my_msg.set("Escribe tu mensaje aqui")
        self.scrollbar = tkinter.Scrollbar(self.messages_frame)
        self.scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.msg_list = tkinter.Listbox(self.messages_frame, height=15,
                                        width=50,
                                        yscrollcommand=self.scrollbar.set)
        self.msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
        self.msg_list.pack()
        self.messages_frame.pack()
        self.entry_field = tkinter.Entry(self.master, textvariable=self.my_msg)
        self.entry_field.bind("<Return>", self.send)
        self.entry_field.pack()
        self.send_button = tkinter.Button(
            self.master, text="Enviar", command=self.send)
        self.send_button.pack()
        self.send_file_button = tkinter.Button(
            self.master, text="Enviar Archivo", command=self.send_file)
        self.send_file_button.pack()
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Funcion para el cierre de la ventana de comunicacion"""
        global continue_receiving
        self.parent.connect_server_button.config(state="normal")
        self.my_msg.set("{quit}")
        self.send()
        print("Comunicacion parada")
        del self.parent.child_list[self.client_to]
        continue_receiving = False

    def send(self):
        msg = self.my_msg.get()
        self.my_msg.set("")
        if msg == "{quit}":
            # para cerrar la comunicacion
            if len(self.parent.child_list) == 1:
                client_socket.send(bytes(msg, "utf8"))
                client_socket.close()
            self.master.destroy()
        elif self.parent.is_broadcast is True:
            # Comprobar si enviamos un mensaje de broadcast
            client_socket.send(
                bytes("broadcast|"+self.my_name+"|"+msg, "utf8"))
            self.msg_list.insert(tkinter.END, self.my_name+" Broadcast: "+msg)
        elif self.parent.is_secure is True:
            # comprobamos si enviamos un mensaje encriptado
            self.msg_list.insert(tkinter.END, self.my_name+": "+msg)
            msg = cr.encrypt(msg, key).decode("utf-8")
            clients_to_send = "|".join(other_client_list)
            print(clients_to_send)
            client_socket.send(
                bytes(clients_to_send+"|"+self.my_name+"|"+msg, "utf8"))
        # enviamos un mensaje normal
        else:
            client_socket.send(
                bytes(self.client_to+"|"+self.my_name+"|"+msg, "utf8"))
            self.msg_list.insert(tkinter.END, self.my_name+": "+msg)

    def send_file(self):
        self.master.filename = filedialog.askopenfilename(
            initialdir="/", title="Select file",
            filetypes=(("jpeg files", "*.jpg"),
                       ("all files", "*.*")))
        file_name = self.master.filename
        print(file_name)
        f = open(file_name, 'rb')
        chunk = f.read(1024)
        client_socket.send(bytes("file|"+self.client_to+"|" +
                                 file_name.split('/')[-1], "utf8"))
        while (chunk):
            client_socket.send(chunk)
            print('Sent ', repr(chunk))
            chunk = f.read(1024)
        f.close()
        print("done sending to server")


def receive(app):
    """Funcion que maneja los mensajes recividos"""
    global continue_receiving
    while continue_receiving:
        try:
            msg = client_socket.recv(BUFSIZE).decode("utf8")
            msg_decoded = msg.split('|')
            print("Mensaje recivido: ")
            print(msg_decoded)
            my_name = app.my_client_name.get()
            # comprobar si es el usuario indicado
            if msg_decoded[0] == my_name:
                # comprobar si es necesario desencriptar el mensaje
                msg = msg_decoded[1]+": " + msg_decoded[2]
                if app.is_secure is True:
                    msg = cr.decrypt(
                        bytes(msg_decoded[2], "utf-8"), key).decode("utf-8")
                    msg = msg_decoded[1]+": " + msg

                if app.is_client_connected is True:
                    for child in app.child_list.values():
                        child.msg_list.insert(tkinter.END, msg)

            # comprobar si es que es un mensaje de broadcast
            elif msg_decoded[0] == "broadcast" and msg_decoded[1] != my_name\
                    and app.is_broadcast is True:
                msg = "Mensaje Broadcast de: " + \
                    msg_decoded[1]+": "+msg_decoded[2]

                if app.is_client_connected is True:
                    for child in app.child_list.values():
                        child.msg_list.insert(tkinter.END, msg)
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
                app.users_list.insert(tkinter.END, msg_decoded[1])

        except OSError:  # Manejo de excepciones.
            break


root = tkinter.Tk()
app = ControlWindow(root)
root.mainloop()
