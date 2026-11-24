import http.server
import socket

import pytest

from agent_dish.cli import DEFAULT_PORT, bind


class Quiet(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass


def test_the_requested_port_is_used_exactly():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    free = probe.getsockname()[1]
    probe.close()
    server = bind("127.0.0.1", free, Quiet)
    try:
        assert server.server_address[1] == free
    finally:
        server.server_close()


def test_a_busy_port_stops_with_a_clear_message_instead_of_moving():
    taken = socket.socket()
    taken.bind(("127.0.0.1", 0))
    taken.listen()
    busy = taken.getsockname()[1]
    try:
        with pytest.raises(SystemExit) as stopped:
            bind("127.0.0.1", busy, Quiet)
        message = str(stopped.value)
        assert f"port {busy} is already in use" in message and "--port" in message
    finally:
        taken.close()


def test_the_default_port_is_static():
    assert DEFAULT_PORT == 3474
