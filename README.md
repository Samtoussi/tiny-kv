# TinyKV

TinyKV is a small Redis-inspired key-value server built from scratch in Python.

The project was created as a systems programming exercise to explore what happens underneath a database server: TCP connections, command parsing, concurrency, in-memory state, persistence, crash recovery, and process lifecycle.

## Features

- TCP server using Python sockets
- Multiple concurrent clients using threads
- Thread-safe shared state
- Simple text-based command protocol
- Append-only file (AOF) persistence
- AOF replay for recovery after restart
- AOF compaction
- Graceful shutdown with SIGINT and SIGTERM
- Automated tests using Python's `unittest`

## Commands

```text
SET <key> <value>
GET <key>
DEL <key>
INCR <key>
COMPACT
```

Example:

```text
SET producer Sam
OK

GET producer
Sam

SET views 100
OK

INCR views
101
```

## How it works

TinyKV keeps its current state in an in-memory Python dictionary.

Write operations are also appended to `tinykv.aof`. When the server starts, it replays the AOF to reconstruct the in-memory state.

```text
Client
  │
  ▼
TCP socket
  │
  ▼
Command engine
  │
  ├──► In-memory store
  │
  └──► Append-only file
             │
             ▼
        Recovery on restart
```

`COMPACT` rewrites the append-only file from the current in-memory state, removing historical operations that are no longer needed.

## Running TinyKV

Start the server:

```bash
python3 server.py
```

Connect from another terminal:

```bash
nc 127.0.0.1 6379
```

Then send commands:

```text
SET name Samimus
GET name
```

Stop the server with `Ctrl+C`.

## Tests

Run the test suite with:

```bash
python3 -m unittest
```

The tests cover the core command operations and AOF recovery.

## Why I built this

TinyKV is a learning project rather than a production database.

The goal was to build enough of a key-value server from scratch to understand concepts such as sockets, message framing, threads, locks, persistence, append-only logs, recovery, compaction, durability, and graceful process shutdown.