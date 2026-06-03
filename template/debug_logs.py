import os

from dotenv import load_dotenv
from e2b import Sandbox

load_dotenv()

alias = os.getenv("E2B_DEBUG_TEMPLATE", "code-interpreter-debug")

sbx = Sandbox.create(template=alias, timeout=600)
print(f"sandbox: {sbx.sandbox_id}")

CMDS = [
    "systemctl --no-pager status jupyter || true",
    "systemctl --no-pager status code-interpreter || true",
    "journalctl --no-pager -u jupyter || true",
    "journalctl --no-pager -u code-interpreter || true",
    "curl -s -o /dev/null -w 'jupyter :8888 -> %{http_code}\\n' http://localhost:8888/api/status || true",
    "curl -s -o /dev/null -w 'server  :49999 -> %{http_code}\\n' http://localhost:49999/health || true",
]

try:
    for cmd in CMDS:
        print(f"\n===== $ {cmd} =====")
        try:
            result = sbx.commands.run(f"sudo bash -lc {cmd!r}", timeout=60)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("[stderr]", result.stderr)
        except Exception as e:
            # Keep going so one slow/failed command doesn't skip the rest.
            print(f"[command failed] {e}")
finally:
    sbx.kill()
