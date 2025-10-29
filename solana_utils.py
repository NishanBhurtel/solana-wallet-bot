from solana.rpc.api import Client
from solders.pubkey import Pubkey
import sys

SOLANA_URL = "https://api.devnet.solana.com"
client = Client(SOLANA_URL)


def _to_pubkey(address):
    """Normalize a string or Pubkey-like input to a solders.Pubkey."""
    if isinstance(address, Pubkey):
        return address
    if isinstance(address, str):
        return Pubkey.from_string(address)
    raise TypeError("address must be a str or solders.pubkey.Pubkey")


def get_balance(wallet_address):
    """Return SOL balance (float) for `wallet_address` or None on error.

    Accepts either a base58 string or a solders.pubkey.Pubkey.
    """
    try:
        pk = _to_pubkey(wallet_address)
        resp = client.get_balance(pk)

        # resp may be a GetBalanceResp dataclass-like object in newer solana
        # libraries. Try a few ways to extract lamports safely.
        lamports = None
        # dataclass / object attribute
        if hasattr(resp, "value"):
            lamports = resp.value
        # named tuple / dict-like
        elif hasattr(resp, "__getitem__"):
            try:
                lamports = resp["result"]["value"]
            except Exception:
                lamports = None

        if lamports is None:
            raise ValueError(f"unexpected response from get_balance: {resp}")

        sol = lamports / 1_000_000_000
        return sol
    except Exception as e:
        # Print to stderr to aid debugging in container, but return None to keep
        # the bot's existing behavior.
        print("solana_utils.get_balance error:", repr(e), file=sys.stderr)
        return None


def request_airdrop(wallet_address, sol_amount: float = 1.0):
    """Request airdrop of `sol_amount` SOL to `wallet_address` on devnet.

    Returns a dict with keys:
      - success: bool
      - signature: str (if available)
      - message: human-friendly message
    """
    try:
        pk = _to_pubkey(wallet_address)
        lamports = int(sol_amount * 1_000_000_000)
        resp = client.request_airdrop(pk, lamports)

        # Extract signature from possible response shapes
        signature = None
        if hasattr(resp, "value"):
            signature = resp.value
        elif isinstance(resp, dict):
            signature = resp.get("result") or resp.get("signature")

        # Try to confirm the transaction if we have a signature
        if signature:
            try:
                client.confirm_transaction(signature)
            except Exception:
                # confirmation failed or not supported; still return signature
                pass

        return {"success": True, "signature": signature, "message": "Airdrop requested."}
    except Exception as e:
        import sys

        print("solana_utils.request_airdrop error:", repr(e), file=sys.stderr)
        return {"success": False, "signature": None, "message": str(e)}


def get_sol_price(vs_currency: str = "usd"):
    """Fetch current SOL price from CoinGecko (simple, no API key).

    Returns price as float in the requested vs_currency, or None on error.
    """
    try:
        import requests

        url = (
            "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies="
            + vs_currency
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = data.get("solana", {}).get(vs_currency)
        if price is None:
            raise ValueError(f"unexpected price response: {data}")
        return float(price)
    except Exception as e:
        import sys

        print("solana_utils.get_sol_price error:", repr(e), file=sys.stderr)
        return None


def get_transaction(signature: str):
    """Fetch transaction info for a given signature from devnet.

    Returns a dict summary or None on error / not found.
    """
    try:
        resp = client.get_transaction(signature)

        # Normalize to a dict-like value
        value = None
        if hasattr(resp, "value"):
            value = resp.value
        elif isinstance(resp, dict):
            value = resp.get("result") or resp.get("value")

        if not value:
            return None

        # Extract common fields safely
        slot = value.get("slot") if isinstance(value, dict) else getattr(value, "slot", None)
        meta = value.get("meta") if isinstance(value, dict) else getattr(value, "meta", None)
        transaction = (
            value.get("transaction") if isinstance(value, dict) else getattr(value, "transaction", None)
        )

        # signatures
        sigs = None
        if transaction is not None:
            if isinstance(transaction, dict):
                sigs = transaction.get("signatures") or []
            else:
                try:
                    sigs = list(transaction.signatures)
                except Exception:
                    sigs = None

        # meta summary
        err = None
        fee = None
        pre_bal = None
        post_bal = None
        if meta is not None:
            if isinstance(meta, dict):
                err = meta.get("err")
                fee = meta.get("fee")
                pre_bal = meta.get("preBalances")
                post_bal = meta.get("postBalances")
            else:
                err = getattr(meta, "err", None)
                fee = getattr(meta, "fee", None)
                pre_bal = getattr(meta, "pre_balances", None) or getattr(meta, "preBalances", None)
                post_bal = getattr(meta, "post_balances", None) or getattr(meta, "postBalances", None)

        return {
            "slot": slot,
            "signatures": sigs,
            "err": err,
            "fee": fee,
            "preBalances": pre_bal,
            "postBalances": post_bal,
        }
    except Exception as e:
        import sys

        print("solana_utils.get_transaction error:", repr(e), file=sys.stderr)
        return None


def generate_wallet():
    """Generate a new Ed25519 keypair and return a dict with address and secret.

    Returns:
      {"address": <base58 str>, "secret_b64": <base64 of keypair bytes>, "secret_hex": <hex>}

    Note: keep the secret safe; do not commit it to source control.
    """
    try:
        from solders.keypair import Keypair
        import base64

        kp = Keypair()
        addr = str(kp.pubkey())
        kb = kp.to_bytes()  # 64 bytes: secret + pub
        b64 = base64.b64encode(kb).decode()
        hexs = kb.hex()
        return {"address": addr, "secret_b64": b64, "secret_hex": hexs}
    except Exception as e:
        import sys

        print("solana_utils.generate_wallet error:", repr(e), file=sys.stderr)
        return None
