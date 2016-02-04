import unittest
import client
from tkinter import Tk
from unittest.mock import patch


class TestClient(unittest.TestCase):
    @patch('socket.socket')
    def test_send(self, mock_socket):
        test_client = client.Client(Tk())
        mock_socket.send.return_value = 'TESTING'.__len__()
        mock_socket.connect.return_value = True
        test_client.socket = mock_socket
        test_client.send('TESTING')
        mock_socket.send.assert_called_with(unittest.mock.ANY)
        # mock_socket.connect.assert_called_with(unittest.mock.ANY)


if __name__ == '__main__':
    unittest.main()
