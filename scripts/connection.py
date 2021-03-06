import os

os.chdir('C:/Users/User/PycharGame')

import pickle
import socket
import logging
from threading import Thread
from scripts.chat import get_config_value, Chat

if get_config_value('game', 'debug'):
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%X')
else:
    logging.basicConfig(format='[%(asctime)s] %(message)', datefmt='%H:%M:%S,%f')


class Server:

    def __init__(self, ip='localhost', port=None, PLAYER_MAX=10):
        if ip is None: ip = get_config_value('server', 'ip')
        if port is None: port = get_config_value('server', "port")
        self.array_address = []
        self.message_to_client = 'default_message'
        self.client_message = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((ip, port))
        self.socket.listen(PLAYER_MAX)
        logging.info(f'Successful create server - {ip}:{port}. Max_player={PLAYER_MAX}')

    def loop(self):
        while True:
            conn, address = self.socket.accept()
            if address[0] not in self.array_address:
                logging.info(f'New player: {address[0]}:{address[1]}')
                self.array_address.append(address[0])
            data = conn.recv(2**15)
            try:
                data = pickle.loads(data)
            except EOFError:
                logging.info(f'data is {data}, not convert type')
                data = ''
            logging.debug(f'Data server - {data}, type={type(data)}')
            if data:
                if self.client_message is None:
                    self.client_message = [data]
                else:
                    self.client_message.append(data)
            conn.send(pickle.dumps(self.message_to_client))
            self.message_to_client = 'default_message'
            conn.close()


class Client:

    def __init__(self, server_ip=None, server_port=None):
        if server_ip is None: server_ip = get_config_value('server', 'ip')
        if server_port is None: server_port = get_config_value('server', 'port')
        self.ip = server_ip
        self.port = server_port
        self.server_message = None
        self.connection()

    def send(self, message):
        bin_obj = pickle.dumps(message)
        self.sock.send(bin_obj)
        data = self.sock.recv(2**15)
        data = pickle.loads(data)
        logging.debug(f'Client data - {data}')
        if data and data != 'default_message':
            if self.server_message is None:
                self.server_message = [data]
            else:
                self.server_message.append(data)
        self.sock.close()
        self.connection()

    def connection(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
        except ConnectionError:
            logging.exception(f'Failed connection server.')


class ConnectionManager:

    def __init__(self, chat: Chat, player, server_: Server = None, client_: Client = None):
        if server_ is not None and client_ is not None:
            raise TypeError('Connection is not server and client')
        if server_ is None and client_ is None:
            raise TypeError('Add client or server')
        self.player = player
        self.chat = chat
        self.server = server_
        self.client = client_
        self.message_to_server = None
        if self.client:
            self.message_to_server = ('player', player)
        else:
            server_.message_to_client = ('player', player)
        self.s = 0

    def update(self) -> object:
        if self.client:  # Отправляем запрос серверу
            self.client.send(self.message_to_server)
            self.message_to_server = None

        if self.client:  # Считываем сообщения от сервера
            mess = self.client.server_message
            self.client.server_message = None

        if self.server:  # Считываем сообщения от клиента
            mess = self.server.client_message
            self.server.client_message = None

        if type(mess) == list:
            for m in mess:
                if type(m) == list:
                    mess.extend(m)
                    del mess[mess.index(m)]
                if type(m) == tuple and m[0] == 'MESS':
                    self.local_chat_update(m)
        return mess if mess is not None else []

    def chat_update(self, name, message):
        if self.client:
            self.client.send(('MESS', name, message))
        else:
            self.server.message_to_client = ('MESS', name, message)

    def local_chat_update(self, mess):
        name = self.chat.name
        self.chat.name, self.chat.message = mess[1:]
        self.chat.send_message(translate_message=False)
        self.chat.name, self.chat.message = name, ''

    def get_message(self) -> object:
        if self.server:
            return self.server.message_to_client
        else:
            return self.message_to_server

    def set_message(self, value) -> None:
        if self.server:
            if self.server.message_to_client != 'default_message' \
                    and self.server.message_to_client not in value:
                pass
                # logging.warning(f'Попытка изменить сообщения для клиента с {self.server.message_to_client} на {value}')
            self.server.message_to_client = value
        else:
            if self.message_to_server is not None and \
                    self.message_to_server not in value:
                pass
                # logging.warning(f'Попытка изменить сообщения для сервера с {self.server.message_to_server} на {value}')
            self.message_to_server = value


# Test
if __name__ == '__main__':
    server = Server()
    Thread(target=server.loop).start()
    client = Client()
    client.send('я люблю каждый')
    client.send('kfjkfjfkjf')
    client.send('kfjkfjfkjf')
