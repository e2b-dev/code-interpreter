#!/bin/bash
# Readiness check for the Code Interpreter server: is Jupyter still the same
# instance the server started against?
#
# The server opens kernel websockets while booting, so a replaced Jupyter
# leaves it holding handles to kernels that no longer exist. Reporting that as
# unhealthy is what gets the server recycled alongside Jupyter, the way
# systemd's PartOf=jupyter.service used to.
#
# Everything else has to report healthy. process-compose keeps probing across a
# restart (initial_delay_seconds only covers the first start), so a check that
# fails while the server boots would restart it forever.

INSTANCE_FILE=/run/jupyter-instance

# Nothing recorded yet: the server is still starting and hasn't picked the
# Jupyter it will attach to.
recorded=$(cat "$INSTANCE_FILE" 2>/dev/null) || exit 0
[ -n "$recorded" ] || exit 0

# Jupyter unreachable: it has its own supervision, and until it answers again
# there's no way to tell whether it was replaced.
started=$(curl -fsS -m 2 "http://localhost:8888/api/status" 2>/dev/null | jq -r '.started')
[ -n "$started" ] && [ "$started" != "null" ] || exit 0

# A mismatch is sticky: every check fails until the server restarts and
# jupyter-healthcheck.sh records the instance it reconnected to.
[ "$started" = "$recorded" ]
