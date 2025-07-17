# Pumpfun/Pumpswap NATS Starter Template (Python)

This repo shows how to **quickly connect to the Pumpfun & Pumpswap on-chain Solana data streams** that are delivered over NATS.

---

## 🏗  Project layout

```
.
├── main.py             # Minimal async consumer / JetStream durable example
├── requirements.txt    # Python packages pinned to known-good versions
└── .env.example        # Optional env vars so you don’t put secrets in git
```

---

## ⚡️ Quick start

1.  Clone / copy the template:

    ```bash
    git clone https://github.com/your-org/nats-python-starter.git
    cd nats-python-starter
    ```

2.  Create a virtual env & install dependencies:

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  Copy `.env.example` → `.env` and fill in **either** `NATS_CREDS` **or** the `NATS_JWT` + `NATS_NKEY` pair plus your stream subject:

    ```env
    NATS_SERVER=nats://edge.pump.fun:4223
    NATS_CREDS=/absolute/path/to/user.creds
    # NATS_JWT=/path/user.jwt
    # NATS_NKEY=/path/user.nk
    NATS_SUBJECT=basic.>
    ```

    * Credentials are issued by the Pumpfun User Management API (`/api/users`).
    * Never commit creds / seeds to git!

4.  Run the consumer (no CLI flags needed – everything is read from `.env` / env vars):

    ```bash
    python main.py
    ```

Messages will stream in real-time and be printed to stdout. Press `Ctrl-C` to disconnect cleanly.

---

## 🌱 Environment variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `NATS_SERVER` | NATS server URL | `nats://edge.pump.fun:4223` |
| `NATS_CREDS` | Path to creds file (preferred auth) | `/home/user/basic.creds` |
| `NATS_JWT` / `NATS_NKEY` | Paths to JWT + NKey seed (advanced auth) | `/jwt/u.jwt`, `/jwt/u.nk` |
| `NATS_SUBJECT` | Subject or wildcard to stream | `basic.>` |

---

## 📝 Notes & best practices

* The **credential file** bundles the user JWT **and** the NKey seed.  It’s the easiest way to authenticate.
* If you prefer to keep secrets split, pass `--jwt` and `--nkey` instead of `--creds`.
* All examples use the official `nats-py` client.
* This template **always** uses JetStream with an **ephemeral push consumer** – no cleanup required.
* If you wish to replay historical data you can add a durable consumer in your own code, but for live pricing a push consumer is the lightest weight option.
* Remember: **Basic tier** can only read `basic.*` subjects, **Plus/Pro** can read both `basic.*` and `premium.*`.

---

## 📚 Helpful links

* Official client docs: https://pynats.docs.io / https://github.com/nats-io/nats.py
* Pumpfun API docs: (internal) <https://pump.fun/docs>
* NATS by Example: https://natsbyexample.com/

---

_MIT © 2025 Pumpfun_