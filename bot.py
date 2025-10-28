import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from solana_utils import get_balance

# Load Telegram token
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

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

# Main
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))

print("Bot is running...")
app.run_polling()
