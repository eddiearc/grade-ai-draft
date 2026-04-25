import importlib.util
from pathlib import Path
import unittest


SERVER_PATH = Path(__file__).resolve().parents[1] / "server.py"
SPEC = importlib.util.spec_from_file_location("ai_redraft_server", SERVER_PATH)
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class FakeClock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class UiHeartbeatTests(unittest.TestCase):
    def test_no_shutdown_before_any_browser_heartbeat(self):
        clock = FakeClock()
        heartbeat = server.UiHeartbeat(clock, grace_seconds=5)

        clock.advance(60)

        self.assertFalse(heartbeat.should_shutdown())

    def test_shutdown_after_heartbeat_grace_expires(self):
        clock = FakeClock()
        heartbeat = server.UiHeartbeat(clock, grace_seconds=5)

        heartbeat.beat()
        clock.advance(4.9)
        self.assertFalse(heartbeat.should_shutdown())

        clock.advance(0.2)
        self.assertTrue(heartbeat.should_shutdown())

    def test_new_heartbeat_resets_shutdown_timer(self):
        clock = FakeClock()
        heartbeat = server.UiHeartbeat(clock, grace_seconds=5)

        heartbeat.beat()
        clock.advance(4)
        heartbeat.beat()
        clock.advance(4)
        self.assertFalse(heartbeat.should_shutdown())

        clock.advance(2)
        self.assertTrue(heartbeat.should_shutdown())


class CompletionExitCodeTests(unittest.TestCase):
    def test_browser_close_is_not_successful_completion(self):
        self.assertEqual(server.exit_code_for_result({"closed": True}), 2)

    def test_done_is_successful_completion(self):
        self.assertEqual(server.exit_code_for_result({"count": 1}), 0)


if __name__ == "__main__":
    unittest.main()
