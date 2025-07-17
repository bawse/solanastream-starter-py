"""Minimal Pumpfun/Pumpswap NATS consumer.

Supports:
  * creds file authentication (preferred)
  * raw JWT + NKey seed authentication
  * plain core NATS subscriptions OR JetStream durable pull consumers

Run `python main.py --help` for CLI usage.
"""

from __future__ import annotations

import asyncio
import argparse
import os
from typing import Optional, Callable, Awaitable, Tuple

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


async def core_subscription(nc: nats.NATS, subject: str, queue: Optional[str] = None):
    """Simple async callback printing each received message."""

    async def _cb(msg):  # type: ignore
        print(f"[{msg.subject}] {msg.data.decode()} | headers={dict(msg.headers) if msg.headers else '{}'}")

    await nc.subscribe(subject, queue=queue, cb=_cb)
    print(f"❯ listening on '{subject}' (queue={queue})… press Ctrl-C to exit")

    try:
        while True:
            await asyncio.sleep(3600)  # keep task alive
    except asyncio.CancelledError:
        pass


async def jetstream_subscription(nc: nats.NATS, subject: str, durable: str):
    """Create / attach to a durable pull consumer and print messages."""

    js = nc.jetstream()

    # pull_subscribe will create the consumer if it does not yet exist.
    sub = await js.pull_subscribe(subject, durable=durable, manual_ack=True)

    print(f"❯ connected to JetStream durable '{durable}' on subject '{subject}'.")
    while True:
        msgs = await sub.fetch(10, timeout=5)
        for msg in msgs:
            print(f"[{msg.subject}] {msg.seq}: {msg.data.decode()}")
            await msg.ack()


async def run_async(args):
    connect_opts: dict = {}

    if args.creds:
        connect_opts["user_credentials"] = args.creds
    elif args.jwt and args.nkey:
        # Raw JWT + NKey auth
        jwt_cb, sig_cb = build_jwt_auth(args.jwt, args.nkey)
        connect_opts["user_jwt_cb"] = jwt_cb
        connect_opts["signature_cb"] = sig_cb
    else:
        raise SystemExit("Error: must supply either --creds or --jwt AND --nkey")

    servers = [args.server]
    print(f"✈︎ connecting to {servers} …")
    try:
        nc = await nats.connect(
            servers=servers,
            error_cb=lambda e: print("NATS error:", e),
            **connect_opts,
        )
    except (ConnectionClosedError, TimeoutError, NoServersError) as e:
        raise SystemExit(f"Could not connect to NATS server: {e}") from e

    print("✅ connected!")

    if args.jetstream:
        await jetstream_subscription(nc, args.subject, args.durable or "pump_consumer")
    else:
        await core_subscription(nc, args.subject, args.queue)

    await nc.drain()


def parse_args():  # noqa: D401
    "Return CLI parsed args."  # noqa: D401
    p = argparse.ArgumentParser(description="Pumpfun/Pumpswap NATS consumer (Python)")
    env = os.getenv

    p.add_argument("--server", default=env("NATS_SERVER", DEFAULT_SERVER))
    p.add_argument("--creds", default=env("NATS_CREDS"))
    p.add_argument("--jwt",   default=env("NATS_JWT"))
    p.add_argument("--nkey",  default=env("NATS_NKEY"))

    p.add_argument("--subject", default=env("NATS_SUBJECT", "basic.>"))
    p.add_argument("--queue",   default=env("NATS_QUEUE"))

    p.add_argument("--jetstream", action="store_true", default=env("NATS_JETSTREAM", "").lower() == "true",
                   help="Use JetStream pull durable instead of plain SUB")
    p.add_argument("--durable", default=env("NATS_DURABLE"), help="Durable consumer name (JetStream)")

    return p.parse_args()


def main():  # noqa: D401
    "Entry point."  # noqa: D401
    args = parse_args()
    try:
        asyncio.run(run_async(args))
    except KeyboardInterrupt:
        print("\nInterrupted – shutting down…")


if __name__ == "__main__":
    main()