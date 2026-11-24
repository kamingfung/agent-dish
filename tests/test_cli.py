import http.server
import socket

import pytest

from agent_dish.cli import DEFAULT_PORT, bind


class Quiet(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass


def free_port():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


def test_the_primary_port_is_used_when_it_is_free():
    port = free_port()
    server, note = bind("127.0.0.1", port, Quiet)
    try:
        assert server.server_address[1] == port and note is None
    finally:
        server.server_close()


def test_a_busy_primary_port_falls_back_to_a_random_free_one_and_says_so():
    taken = socket.socket()
    taken.bind(("127.0.0.1", 0))
    taken.listen()
    busy = taken.getsockname()[1]
    try:
        server, note = bind("127.0.0.1", busy, Quiet)
        try:
            used = server.server_address[1]
            assert used not in (0, busy)
            assert note == f"port {busy} is busy (is agent-dish already running there?), using {used}"
        finally:
            server.server_close()
    finally:
        taken.close()


def test_port_zero_means_random_and_is_not_a_fallback_case():
    server, note = bind("127.0.0.1", 0, Quiet)
    try:
        assert server.server_address[1] > 0 and note is None
    finally:
        server.server_close()


def test_the_primary_port_is_fixed():
    assert DEFAULT_PORT == 3474


def test_an_unbindable_host_still_raises_rather_than_looping():
    with pytest.raises(OSError):
        bind("203.0.113.1", free_port(), Quiet)  # a documentation address no local interface owns
