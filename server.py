import os
import signal
import socket
import threading

AOF_FILE = "tinykv.aof"
TEMP_AOF_FILE = "tinykv.aof.tmp"

store = {}
store_lock = threading.Lock()

shutdown_event = threading.Event()
client_sockets = set()
clients_lock = threading.Lock()


def append_to_aof(command):
    with open(AOF_FILE, "a") as file:
        file.write(command + "\n")
        file.flush()
        os.fsync(file.fileno())


def compact_aof():
    with open(TEMP_AOF_FILE, "w") as file:
        for key, value in store.items():
            file.write(f"SET {key} {value}\n")

        file.flush()
        os.fsync(file.fileno())

    os.replace(TEMP_AOF_FILE, AOF_FILE)


def execute_command(message, replay=False):
    if not message:
        return "ERROR: empty command"

    parts = message.split(" ", 2)
    command = parts[0].upper()

    if command == "SET":
        if len(parts) < 3:
            return "ERROR: SET requires a key and value"

        key = parts[1]
        value = parts[2]

        with store_lock:
            store[key] = value

            if not replay:
                append_to_aof(message)

        return "OK"

    elif command == "GET":
        if len(parts) < 2:
            return "ERROR: GET requires a key"

        key = parts[1]

        with store_lock:
            value = store.get(key)

        if value is not None:
            return value

        return "(nil)"

    elif command == "DEL":
        if len(parts) < 2:
            return "ERROR: DEL requires a key"

        key = parts[1]

        with store_lock:
            if key in store:
                del store[key]

                if not replay:
                    append_to_aof(message)

                return "OK"

        return "(nil)"

    elif command == "INCR":
        if len(parts) < 2:
            return "ERROR: INCR requires a key"

        key = parts[1]

        with store_lock:
            if key not in store:
                store[key] = "0"

            try:
                value = int(store[key])
            except ValueError:
                return "ERROR: value is not an integer"

            value += 1
            store[key] = str(value)

            if not replay:
                append_to_aof(message)

        return str(value)

    elif command == "COMPACT":
        if replay:
            return "OK"

        with store_lock:
            compact_aof()

        return "OK"

    else:
        return "ERROR: unknown command"


def load_aof():
    if not os.path.exists(AOF_FILE):
        return

    with open(AOF_FILE, "r") as file:
        for line in file:
            command = line.strip()

            if command:
                execute_command(command, replay=True)


def handle_client(client_socket, client_address):
    print(f"Client connected from {client_address}")

    with clients_lock:
        client_sockets.add(client_socket)

    buffer = ""

    try:
        while not shutdown_event.is_set():
            data = client_socket.recv(1024)

            if not data:
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                message = message.strip()

                print(f"Received from {client_address}: {message}")

                response = execute_command(message)

                client_socket.sendall(
                    f"{response}\n".encode("utf-8")
                )

    except OSError:
        # Expected if the socket is closed during shutdown.
        pass

    finally:
        with clients_lock:
            client_sockets.discard(client_socket)

        client_socket.close()
        print(f"Client disconnected: {client_address}")


def handle_shutdown(signum, frame):
    print("\nShutdown requested...")
    shutdown_event.set()


load_aof()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.setsockopt(
    socket.SOL_SOCKET,
    socket.SO_REUSEADDR,
    1,
)

server_socket.settimeout(1.0)
server_socket.bind(("127.0.0.1", 6379))
server_socket.listen()

signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

print("TinyKV listening on 127.0.0.1:6379...")

try:
    while not shutdown_event.is_set():
        try:
            client_socket, client_address = server_socket.accept()

            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
            )

            client_thread.start()

        except socket.timeout:
            continue

finally:
    print("Shutting down TinyKV...")

    server_socket.close()

    with clients_lock:
        sockets_to_close = list(client_sockets)

    for client_socket in sockets_to_close:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        client_socket.close()

    print("TinyKV stopped.")