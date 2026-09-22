import socket
import threading

store = {}
store_lock = threading.Lock()


def handle_client(client_socket, client_address):
    print(f"Client connected from {client_address}")

    buffer = ""

    while True:
        data = client_socket.recv(1024)

        if not data:
            break

        buffer += data.decode("utf-8")

        while "\n" in buffer:
            message, buffer = buffer.split("\n", 1)
            message = message.strip()

            print(f"Received from {client_address}: {message}")

            if not message:
                client_socket.sendall(b"ERROR: empty command\n")
                continue

            parts = message.split(" ", 2)
            command = parts[0].upper()

            if command == "SET":
                if len(parts) < 3:
                    client_socket.sendall(
                        b"ERROR: SET requires a key and value\n"
                    )
                    continue

                key = parts[1]
                value = parts[2]

                with store_lock:
                    store[key] = value

                client_socket.sendall(b"OK\n")

            elif command == "GET":
                if len(parts) < 2:
                    client_socket.sendall(
                        b"ERROR: GET requires a key\n"
                    )
                    continue

                key = parts[1]

                with store_lock:
                    value = store.get(key)

                if value is not None:
                    client_socket.sendall(
                        f"{value}\n".encode("utf-8")
                    )
                else:
                    client_socket.sendall(b"(nil)\n")

            elif command == "DEL":
                if len(parts) < 2:
                    client_socket.sendall(
                        b"ERROR: DEL requires a key\n"
                    )
                    continue

                key = parts[1]

                with store_lock:
                    if key in store:
                        del store[key]
                        deleted = True
                    else:
                        deleted = False

                if deleted:
                    client_socket.sendall(b"OK\n")
                else:
                    client_socket.sendall(b"(nil)\n")

            elif command == "INCR":
                if len(parts) < 2:
                    client_socket.sendall(
                        b"ERROR: INCR requires a key\n"
                    )
                    continue

                key = parts[1]

                with store_lock:
                    if key not in store:
                        store[key] = "0"

                    try:
                        value = int(store[key])
                    except ValueError:
                        client_socket.sendall(
                            b"ERROR: value is not an integer\n"
                        )
                        continue

                    value += 1
                    store[key] = str(value)

                client_socket.sendall(
                    f"{value}\n".encode("utf-8")
                )

            else:
                client_socket.sendall(b"ERROR: unknown command\n")

    client_socket.close()
    print(f"Client disconnected: {client_address}")


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(("127.0.0.1", 6379))
server_socket.listen()

print("TinyKV listening on 127.0.0.1:6379...")

while True:
    client_socket, client_address = server_socket.accept()

    client_thread = threading.Thread(
        target=handle_client,
        args=(client_socket, client_address),
    )

    client_thread.start()