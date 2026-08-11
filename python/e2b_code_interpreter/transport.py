"""HTTP/1.1 transports for Jupyter requests.

# TODO: Remove later
The base SDK's shared transports let ALPN negotiate the HTTP version, which
means HTTP/2 against the sandbox. With HTTP/2, multiple requests are
multiplexed over a single TCP connection, so when a client cancels a request
(e.g. the caller disconnects from the streaming `/execute` endpoint) the
server may not detect the disconnect: only the HTTP/2 stream is cancelled,
the underlying TCP connection stays open.

Forcing HTTP/1.1 keeps the 1:1 mapping between TCP connection and request, so
client disconnects propagate to the server as a TCP close, uvicorn delivers
`http.disconnect`, and long-running executions can be cancelled reliably.

The base SDK has no option for this, so we build the transport ourselves from
the same pieces it uses (its pool tuning and connect-only retry policy) with
`http_version` pinned to HTTP/1.1.
"""

import threading
from typing import Dict, Optional

from pyqwest import HTTPTransport, HTTPVersion, SyncHTTPTransport
from pyqwest.httpx import AsyncPyqwestTransport, PyqwestTransport

from e2b.api import (
    ProxyConfig,
    connection_retries,
    pool_idle_timeout,
    pool_max_idle_per_host,
    proxy_to_config,
)
from e2b.api.client_async import (
    ConnectionRetryTransport as AsyncConnectionRetryTransport,
)
from e2b.api.client_sync import ConnectionRetryTransport as SyncConnectionRetryTransport
from e2b.connection_config import ConnectionConfig

_transport_lock = threading.Lock()
# One transport (= one connection pool) per proxy; None is the direct pool.
# pyqwest transports are thread-safe and loop-independent, so the caches are
# process-global rather than per-thread (sync) or per-event-loop (async).
_sync_transports: Dict[Optional[ProxyConfig], PyqwestTransport] = {}
_async_transports: Dict[Optional[ProxyConfig], AsyncPyqwestTransport] = {}


def _transport_kwargs(proxy: Optional[ProxyConfig]) -> dict:
    return dict(
        # System CA certs, without which TLS through an intercepting proxy
        # fails.
        tls_include_system_certs=True,
        proxy=proxy.to_pyqwest() if proxy is not None else None,
        http_version=HTTPVersion.HTTP1,
        pool_idle_timeout=pool_idle_timeout,
        pool_max_idle_per_host=pool_max_idle_per_host,
        # Redirects belong to the httpx client above, not to reqwest.
        follow_redirects=False,
    )


def get_sync_transport(config: ConnectionConfig) -> PyqwestTransport:
    """The shared HTTP/1.1 transport for synchronous Jupyter requests."""
    proxy = proxy_to_config(config.proxy)
    with _transport_lock:
        transport = _sync_transports.get(proxy)
        if transport is None:
            transport = PyqwestTransport(
                SyncConnectionRetryTransport(
                    SyncHTTPTransport(**_transport_kwargs(proxy)),
                    max_retries=connection_retries,
                )
            )
            _sync_transports[proxy] = transport
        return transport


def get_async_transport(config: ConnectionConfig) -> AsyncPyqwestTransport:
    """The shared HTTP/1.1 transport for asynchronous Jupyter requests."""
    proxy = proxy_to_config(config.proxy)
    with _transport_lock:
        transport = _async_transports.get(proxy)
        if transport is None:
            transport = AsyncPyqwestTransport(
                AsyncConnectionRetryTransport(
                    HTTPTransport(**_transport_kwargs(proxy)),
                    max_retries=connection_retries,
                )
            )
            _async_transports[proxy] = transport
        return transport
