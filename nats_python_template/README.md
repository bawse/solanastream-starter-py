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

3.  Drop your **credential file** ( `*.creds` ) _or_ a **user JWT + NKey seed** somewhere safe on disk.

    * Credentials are issued by the Pumpfun User Management API (`/api/users`).
    * Never commit creds / seeds to git!

4.  Run the consumer:

    ```bash
    python main.py \
      --server nats://edge.pump.fun:4223 \
      --creds  /path/to/user.creds \
      --subject "basic.>"
    ```

    or with separate files:

    ```bash
    python main.py \
      --server nats://edge.pump.fun:4223 \
      --jwt    /path/to/user.jwt \
      --nkey   /path/to/user.nk \
      --subject "premium.trades.*"
    ```

When messages arrive they will be printed to stdout.  Press `Ctrl-C` to exit gracefully.

---

## 🧩 CLI flags

| Flag | Env Var | Description |
|------|---------|-------------|
| `--server` | `NATS_SERVER` | NATS server URL (default `nats://127.0.0.1:4223`) |
| `--creds`  | `NATS_CREDS`  | Path to `*.creds` file (preferred) |
| `--jwt`    | `NATS_JWT`    | Path to user JWT (when not using creds) |
| `--nkey`   | `NATS_NKEY`   | Path to user NKey seed (when not using creds) |
| `--subject`| `NATS_SUBJECT`| Subject / wildcard to subscribe to (default `basic.>`) |
| `--queue`  | `NATS_QUEUE`  | Queue group name (optional) |
| `--jetstream` | `NATS_JETSTREAM` | Treat subject as JetStream stream & create a durable consumer |
| `--durable`   | `NATS_DURABLE`   | Durable consumer name (JetStream only) |

---

## 📝 Notes & best practices

* The **credential file** bundles the user JWT **and** the NKey seed.  It’s the easiest way to authenticate.
* If you prefer to keep secrets split, pass `--jwt` and `--nkey` instead of `--creds`.
* All examples use the official `nats-py` client.
* The `--jetstream` flag shows how to create a **pull consumer** that receives historical data reliably.
* For real-time streaming only, omit `--jetstream` – a plain `SUB` is faster and incurs zero server state.
* Remember: **Basic tier** can only read `basic.*` subjects, **Plus/Pro** can read both `basic.*` and `premium.*`.

---

## 📚 Helpful links

* Official client docs: https://pynats.docs.io / https://github.com/nats-io/nats.py
* Pumpfun API docs: (internal) <https://pump.fun/docs>
* NATS by Example: https://natsbyexample.com/

---

_MIT © 2025 Pumpfun_