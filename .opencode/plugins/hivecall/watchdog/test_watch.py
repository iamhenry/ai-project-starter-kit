import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

WATCH = Path(__file__).with_name("watch.py")
spec = importlib.util.spec_from_file_location("hivecall_watch", WATCH)
watch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watch)


class LoadBBTests(unittest.TestCase):
    def test_valid_binding_still_loads_bb_children(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            binding = home / ".bb/plugins/opencode/task-bound.json"
            binding.parent.mkdir(parents=True)
            binding.write_text(json.dumps({"bindings": {"ses_root": "thr_root"}}))
            calls = []

            def parse_json(args, timeout=8.0):
                calls.append(args)
                if args[:2] == ["thread", "list"]:
                    return ([{"id": "thr_child", "parentThreadId": "thr_root"}], "")
                if args[:2] == ["thread", "show"]:
                    return ({"id": "thr_root", "status": "running"}, "")
                return None, "unexpected call"

            expanduser = lambda path: path.replace("~", str(home), 1) if path.startswith("~") else path
            with patch.object(watch.os.path, "expanduser", side_effect=expanduser), \
                 patch.object(watch.BB, "parse_json", side_effect=parse_json), \
                 patch.object(watch.BB, "command", return_value=("[]", "")):
                result = watch.load_bb("thr_root", [], [])

            self.assertTrue(result["binding_valid"])
            self.assertTrue(result["list_valid"])
            self.assertEqual(result["children"], [{"id": "thr_child", "parentThreadId": "thr_root"}])
            self.assertEqual(calls[0], ["thread", "list", "--json"])


if __name__ == "__main__":
    unittest.main()
