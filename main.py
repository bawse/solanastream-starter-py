"""Minimal Pumpfun/Pumpswap NATS consumer.

Supports:
  * creds file authentication (preferred)
  * raw JWT + NKey seed authentication
  * plain core NATS subscriptions OR JetStream durable pull consumers

Run `python main.py --help` for CLI usage.
"""

from __future__ import annotations

import asyncio
import signal
import os
from typing import Callable, Awaitable, Tuple

import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
from dotenv import load_dotenv

# Optional dependency (only needed when using raw JWT + NKey)
try:
    import nkeys
except ImportError:  # pragma: no cover
    nkeys = None  # type: ignore


load_dotenv()  # read .env if present

DEFAULT_SERVER = os.getenv("NATS_SERVER", "nats://127.0.0.1:4223")

# Subject wildcard to subscribe to (JetStream stream must export it)
DEFAULT_SUBJECT = os.getenv("NATS_SUBJECT", "basic.>")


def build_jwt_auth(jwt_path: str, nkey_path: str) -> Tuple[Callable[[], Awaitable[str]], Callable[[bytes], Awaitable[bytes]]]:
    """Return callbacks for user_jwt_cb and signature_cb options."""
    if nkeys is None:
        raise RuntimeError("Package 'nkeys' required for JWT/NKey auth.\n\n  pip install nkeys")

    async def jwt_cb() -> str:  # noqa: D401
        "Return the user JWT as string."  # noqa: D401
        with open(jwt_path, "r", encoding="utf8") as f:
            return f.read().strip()

    async def sig_cb(nonce: bytes) -> bytes:  # noqa: D401
        "Sign the server nonce using the NKey seed."  # noqa: D401
        with open(nkey_path, "rb") as f:
            seed = f.read().strip()
        kp = nkeys.from_seed(seed)
        return kp.sign(nonce)

    return jwt_cb, sig_cb


async def run():
    """Main async entrypoint using env vars for configuration."""

    # 1. Gather config from env / .env
    server_url = os.getenv("NATS_SERVER", DEFAULT_SERVER)
    creds_path = os.getenv("NATS_CREDS")
    jwt_path = os.getenv("NATS_JWT")
    nkey_path = os.getenv("NATS_NKEY")
    subject = os.getenv("NATS_SUBJECT", DEFAULT_SUBJECT)

    connect_opts: dict = {}

    if creds_path:
        connect_opts["user_credentials"] = creds_path
    elif jwt_path and nkey_path:
        jwt_cb, sig_cb = build_jwt_auth(jwt_path, nkey_path)
        connect_opts["user_jwt_cb"] = jwt_cb
        connect_opts["signature_cb"] = sig_cb
    else:
        raise SystemExit(
            "Missing authentication details. Set NATS_CREDS or NATS_JWT & NATS_NKEY in your environment (see .env.example)."
        )

    print(f"✈︎ Connecting to {server_url} …")
    try:
        nc = await nats.connect(server_url, error_cb=lambda e: print("NATS error:", e), **connect_opts)
    except (ConnectionClosedError, TimeoutError, NoServersError) as e:
        raise SystemExit(f"Could not connect to NATS server: {e}") from e

    print("✅ Connected – setting up JetStream push consumer on", subject)

    js = nc.jetstream()

    # Ephemeral push consumer (no durable). Auto-acks unless manual_ack=True.

    async def _msg_cb(msg):  # type: ignore
        print(f"[{msg.subject}] {msg.data.decode(errors='replace')}")
        try:
            await msg.ack()
        except Exception as ack_err:  # noqa: BLE001
            print("ack error:", ack_err)

    await js.subscribe(subject, cb=_msg_cb)  # push, ephemeral

    # Handle graceful shutdown
    stop_event = asyncio.Event()

    def _signal_handler(*_):
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    print("📡 Listening – press Ctrl+C to exit")
    await stop_event.wait()

    print("Draining connection…")
    await nc.drain()


def main():
    "Entry point that loads .env and runs the async loop."  # noqa: D401
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()