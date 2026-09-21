import socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind(("127.0.0.1", 6379))
server_socket.listen()

print("TinyKV listening on 127.0.0.1:6379...")

store = {}

client_socket, client_address = server_socket.accept()

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

        print(f"Received: {message}")

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

            store[key] = value

            client_socket.sendall(b"OK\n")

        elif command == "GET":
            if len(parts) < 2:
                client_socket.sendall(
                    b"ERROR: GET requires a key\n"
                )
                continue

            key = parts[1]

            if key in store:
                value = store[key]
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

            if key in store:
                del store[key]
                client_socket.sendall(b"OK\n")
            else:
                client_socket.sendall(b"(nil)\n")

        else:
            client_socket.sendall(b"ERROR: unknown command\n")

client_socket.close()