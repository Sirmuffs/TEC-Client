#!/usr/bin/env python
from socket import socket
from queue import Queue
from time import sleep
from threading import Thread
from configparser import ConfigParser
import logging
import time
import re

import hashlib

import requests

from .clientui import ClientUI

__author__ = 'ToothlessRebel'


class Client:
    def __init__(self, master):
        self.log = logging.getLogger(__name__)
        self.log.warning('Starting logger.')
        self.master = master
        self.queue = Queue()
        self.connect = True
        self.config = ConfigParser()
        if self.config.read('config.ini').__len__() < 1:
            raise EnvironmentError
        self.ui = ClientUI(master, self, self.queue, self.send)
        self.socket = socket()
        self.listener = None
        self.session_log_name = time.strftime("%d.%m.%Y-%H.%M.%S.txt")
        self.startup()
        self.master.protocol("WM_DELETE_WINDOW", self.quit)
        self.uname = ''
        self.pwd = ''

    def send(self, command):
        if self.connect:
            total_successful = 0
            while total_successful < command.__len__():
                successful = self.socket.send(bytes(command[total_successful:] + "\r\n", "UTF-8"))
                if successful == 0:
                    raise RuntimeError("Unable to send message.")
                total_successful = total_successful + successful
        else:
            self.ui.parse_output("No connection -- please reconnect to send commands.\n")

    def startup(self):
        self.connect = True
        self.socket = socket()
        self.ui.menu_file.entryconfigure(1, label="Disconnect", command=self.shutdown)
        self.listener = Thread(target=self.listen)
        self.listener.start()
        self.session_log_name = time.strftime("%d.%m.%Y-%H.%M.%S.txt")

    def shutdown(self, completely=False):
        self.connect = False
        socket.close(self.socket)
        if not completely:
            self.ui.menu_file.entryconfigure(1, label="Reconnect", command=self.startup)
            self.ui.parse_output('Connection closed.')

    def quit(self):
        self.shutdown(True)
        self.master.destroy()

    def log_session(self, text):
        log_dir = self.config['logging']['log_directory']
        log_filename = log_dir + self.session_log_name
        with open(log_filename, 'a+') as game_log:
            game_log.write(text)

    def listen(self):
        socket.connect(self.socket, ("tec.skotos.net", 6730))
        self.login_user()
        if self.connect:
            self.log.info('Sending Zealous protocol.')
            self.send("SKOTOS Zealous 0.7.12.2\n")
        while self.connect:
            buffer = ""
            sleep(0)
            try:
                buffer = str(self.socket.recv(4096), encoding='utf8')
            except Exception as exc:
                pass
            buffer = buffer.splitlines()
            if not buffer.__len__() == 0:
                for number, line in enumerate(buffer):
                    if line.find('SECRET') == -1:
                        self.ui.parse_output(line)
                    else:
                        if line.find('SECRET') == 0:
                            secret = line[7:].strip()
                            hash_string = self.uname + self.pwd + secret
                            zealous_hash = hashlib.md5(hash_string.encode('utf-8')).hexdigest()
                            self.send("USER " + self.uname)
                            self.send("SECRET " + secret)
                            self.send("HASH " + zealous_hash)
                            self.send("CHAR ")
                            # After a Zealotry login the server still sends a password prompt. This just responds to
                            # that with a dummy entry.
                            self.send("Nope")
            else:
                break
        if self.connect:
            self.shutdown()

    def login_user(self):
        self.ui.interrupt_input = True
        self.log.debug('Requesting credentials.')
        self.ui.draw_output('\nPlease enter your user name:')
        while self.ui.interrupt_buffer.__len__() < 1 and self.connect:
            sleep(0.5)
        if self.connect:
            self.ui.draw_output('\nPlease enter your password:')
        while self.ui.interrupt_buffer.__len__() < 2 and self.connect:
            sleep(0.5)
        self.log.debug('Attempting to verify credentials.')
        if self.connect:  # If the client has stopped during the pause, don't try and send commands.
            self.ui.draw_output('\nSigning in...')

            # Attempt to Zealotry log in.
            header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/42.0.2311.90 Safari/537.36',
                'Cookie': 'biscuit=test'
            }
            data = {
                'uname': self.ui.interrupt_buffer.popleft(),
                'pwd': self.ui.interrupt_buffer.popleft(),
                'phrase': '',
                'submit': 'true'
            }
            url = 'https://www.skotos.net/user/login.php'
            response = requests.post(url, headers=header, data=data, allow_redirects=False, verify=False)
            self.log.debug('Got a response.')
            try:
                self.uname = re.search('user=(.*?);', response.headers['set-cookie']).group(1)
                self.pwd = re.search('pass=(.*?);', response.headers['set-cookie']).group(1)
            except KeyError:
                self.ui.draw_output('\nIncorrect credentials, please re-enter.')
                self.login_user()
            self.ui.interrupt_input = False
