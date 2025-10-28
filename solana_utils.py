from solana.rpc.api import Client

SOLANA_URL = "https://api.devnet.solana.com"
client = Client(SOLANA_URL)

def get_balance(wallet_address):
    try:
        result = client.get_balance(wallet_address)
        lamports = result["result"]["value"]
        sol = lamports / 1_000_000_000  # Convert lamports to SOL
        return sol
    except Exception as e:
        return None
