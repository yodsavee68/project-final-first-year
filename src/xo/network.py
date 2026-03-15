import socket
import threading
import pickle
import time
import json
from xo.constants import DEFAULT_PORT, DISCOVERY_PORT


class NetworkManager:
    def __init__(self, is_host: bool, ip: str = "127.0.0.1", port: int = DEFAULT_PORT):
        self.is_host = is_host
        self.ip = "0.0.0.0" if is_host else ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow reuse address to prevent "Address already in use" errors during dev
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.conn = None

        self.connected = False
        self.received_data = []  # Queue for data

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            if self.is_host:
                self.sock.bind((self.ip, self.port))
                self.sock.listen(1)
                print(f"Hosting on port {self.port}")
                self.conn, addr = self.sock.accept()
                print(f"Connected to {addr}")
                self.connected = True
            else:
                print(f"Connecting to {self.ip}:{self.port}")
                self.sock.connect((self.ip, self.port))
                self.conn = self.sock
                self.connected = True

            self._receive_loop()
        except Exception as e:
            print(f"Network error: {e}")
            self.connected = False

    def _receive_loop(self):
        while self.connected:
            try:
                data = self.conn.recv(8192)
                if not data:
                    break
                # Append to queue
                self.received_data.append(pickle.loads(data))
            except Exception as e:
                print(f"Receive loop error: {e}")
                break
        self.connected = False
        print("Disconnected")

    def send(self, data):
        if self.connected and self.conn:
            try:
                self.conn.sendall(pickle.dumps(data))
            except Exception as e:
                print(f"Send error: {e}")
                self.connected = False

    def get_data(self):
        if self.received_data:
            return self.received_data.pop(0)
        return None

    def close(self):
        self.connected = False
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        try:
            self.sock.close()
        except Exception:
            pass


class RoomBroadcaster:
    def __init__(self, username: str, port: int = DEFAULT_PORT):
        self.username = username
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # Allows multiple broadcasters on the same machine (for local testing)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            pass

        self.running = False
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def _run(self):
        while self.running:
            try:
                message = json.dumps(
                    {"username": self.username, "port": self.port}
                ).encode("utf-8")
                self.sock.sendto(message, ("<broadcast>", DISCOVERY_PORT))
            except Exception:
                pass
            time.sleep(1)


class RoomListener:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Allow multiple listeners on the same machine
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except AttributeError:
            pass

        try:
            # Try to handle SO_REUSEPORT for Mac/Linux
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:
            pass

        self.sock.bind(("", DISCOVERY_PORT))
        self.sock.settimeout(1.0)
        self.running = False
        self.rooms = {}  # (ip, port): {"username": str, "last_seen": float}
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass

    def get_rooms(self):
        current_time = time.time()
        # Clean up stale rooms (not seen in 3 seconds)
        active_rooms = []
        stale_keys = []

        for key, room_data in self.rooms.items():
            if current_time - room_data["last_seen"] > 3.0:
                stale_keys.append(key)
            else:
                active_rooms.append(
                    {"ip": key[0], "port": key[1], "username": room_data["username"]}
                )

        for key in stale_keys:
            del self.rooms[key]

        return active_rooms

    def _run(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode("utf-8"))

                # We expect dict: {"username": ..., "port": ...}
                if "username" in message and "port" in message:
                    key = (addr[0], message["port"])
                    self.rooms[key] = {
                        "username": message["username"],
                        "last_seen": time.time(),
                    }
            except socket.timeout:
                pass
            except Exception:
                pass
