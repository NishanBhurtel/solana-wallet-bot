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
