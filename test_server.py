import os
import unittest

import server


class TinyKVTests(unittest.TestCase):

    def setUp(self):
        server.store.clear()

        if os.path.exists(server.AOF_FILE):
            os.remove(server.AOF_FILE)

        if os.path.exists(server.TEMP_AOF_FILE):
            os.remove(server.TEMP_AOF_FILE)

    def tearDown(self):
        if os.path.exists(server.AOF_FILE):
            os.remove(server.AOF_FILE)

        if os.path.exists(server.TEMP_AOF_FILE):
            os.remove(server.TEMP_AOF_FILE)

    def test_set_and_get(self):
        self.assertEqual(
            server.execute_command("SET emperor Samimus"),
            "OK",
        )

        self.assertEqual(
            server.execute_command("GET emperor"),
            "Samimus",
        )

    def test_delete(self):
        server.execute_command("SET producer Chatisimus")

        self.assertEqual(
            server.execute_command("DEL producer"),
            "OK",
        )

        self.assertEqual(
            server.execute_command("GET producer"),
            "(nil)",
        )

    def test_increment(self):
        server.execute_command("SET views 100")

        self.assertEqual(
            server.execute_command("INCR views"),
            "101",
        )

        self.assertEqual(
            server.execute_command("GET views"),
            "101",
        )

    def test_aof_recovery(self):
        server.execute_command("SET emperor Samimus")
        server.execute_command("SET views 100")
        server.execute_command("INCR views")

        # Simulate losing the in-memory state.
        server.store.clear()

        # Rebuild the store from the append-only file.
        server.load_aof()

        self.assertEqual(
            server.execute_command("GET emperor"),
            "Samimus",
        )

        self.assertEqual(
            server.execute_command("GET views"),
            "101",
        )


if __name__ == "__main__":
    unittest.main()