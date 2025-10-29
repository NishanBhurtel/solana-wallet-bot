import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from solana_utils import get_balance
from solana_utils import request_airdrop, get_sol_price, get_transaction, generate_wallet

# Load Telegram token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TOKEN or TOKEN.strip() == "" or TOKEN.startswith("YOUR_"):
    raise SystemExit(
        "Please set TELEGRAM_TOKEN in your environment or in a .env file.\n"
        "Create a .env file with: TELEGRAM_TOKEN=<your-telegram-bot-token>"
    )

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send /balance <wallet_address> to check SOL balance on devnet."
    )

# Balance command
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please provide a wallet address.\nUsage: /balance <wallet_address>")
        return
    wallet = context.args[0]
    sol = get_balance(wallet)
    if sol is not None:
        await update.message.reply_text(f"💰 Wallet {wallet} balance: {sol} SOL")
    else:
        await update.message.reply_text("❌ Invalid wallet or unable to fetch balance.")


# Airdrop command: /airdrop <address>
async def airdrop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please provide a wallet address.\nUsage: /airdrop <wallet_address>")
        return
    wallet = context.args[0]
    await update.message.reply_text("⏳ Requesting 1 SOL airdrop on devnet...")
    result = request_airdrop(wallet, sol_amount=1.0)
    if result.get("success"):
        sig = result.get("signature")
        msg = f"✅ Airdrop requested. Signature: {sig}" if sig else "✅ Airdrop requested."
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(f"❌ Airdrop failed: {result.get('message')}")


# Price command: /price
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Fetching SOL price...")
    p = get_sol_price("usd")
    if p is not None:
        await update.message.reply_text(f"💱 SOL price: ${p:,.2f} USD")
    else:
        await update.message.reply_text("❌ Unable to fetch SOL price right now.")


# Transaction info: /tx <signature>
async def tx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Please provide a transaction signature.\nUsage: /tx <signature>")
        return
    sig = context.args[0]
    await update.message.reply_text("⏳ Fetching transaction info...")
    info = get_transaction(sig)
    if not info:
        await update.message.reply_text("❌ Transaction not found or unable to fetch info.")
        return
    # Build a short summary
    slot = info.get("slot")
    err = info.get("err")
    fee = info.get("fee")
    sigs = info.get("signatures")
    pre = info.get("preBalances")
    post = info.get("postBalances")

    msg_lines = [f"🔎 Transaction {sig}"]
    if slot is not None:
        msg_lines.append(f"• slot: {slot}")
    if fee is not None:
        msg_lines.append(f"• fee: {fee}")
    if err:
        msg_lines.append(f"• err: {err}")
    if sigs:
        msg_lines.append(f"• signatures: {', '.join((sigs if isinstance(sigs, (list,tuple)) else [str(sigs)]))}")
    if pre is not None and post is not None:
        msg_lines.append(f"• preBalances: {pre}")
        msg_lines.append(f"• postBalances: {post}")

    await update.message.reply_text("\n".join(msg_lines))


# Generate wallet: /generate
async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 Generating a new wallet (keep the secret safe)...")
    info = generate_wallet()
    if not info:
        await update.message.reply_text("❌ Unable to generate wallet right now.")
        return
    addr = info.get("address")
    secret_b64 = info.get("secret_b64")
    # warn user to keep secret safe
    msg = (
        f"✅ Wallet generated:\nAddress: `{addr}`\nSecret (base64): `{secret_b64}`\n"
        "⚠️ Keep this secret safe. Do not share it publicly."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


# Help command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📚 Available commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/balance <wallet_address> - Show SOL balance on devnet\n"
        "/airdrop <wallet_address> - Request 1 SOL from devnet faucet\n"
        "/price - Get current SOL price (USD)\n"
        "/tx <signature> - Fetch transaction info\n"
        "/generate - Generate a new wallet (returns secret; keep it safe)\n"
    )
    await update.message.reply_text(help_text)

# Main
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("airdrop", airdrop))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("tx", tx))
app.add_handler(CommandHandler("generate", generate))
app.add_handler(CommandHandler("help", help_command))

print("Bot is running...")
app.run_polling()
