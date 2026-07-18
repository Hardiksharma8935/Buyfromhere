from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from src.groups_config import GROUPS

class PremiumUI:
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton("🛒 Buy Groups"), KeyboardButton("👤 Profile")],
            [KeyboardButton("🎬 Demo"), KeyboardButton("📢 Main Channel")],
            [KeyboardButton("💬 Contact Admin")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

    @staticmethod
    def cancel_inline() -> list:
        return [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]

    @staticmethod
    def deposit_to_wallet() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[InlineKeyboardButton("💰 Deposit to Wallet", callback_data="start_deposit_flow")]])

    @staticmethod
    def link_button(text: str, url: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([[InlineKeyboardButton(text, url=url)]])

    @staticmethod
    def currency_selection() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇳 INR (₹)", callback_data="dep_curr_INR"), InlineKeyboardButton("🇺🇸 USD ($)", callback_data="dep_curr_USD")],
            PremiumUI.cancel_inline()
        ])

    @staticmethod
    def payment_methods() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 Crypto", callback_data="dep_meth_Crypto"), InlineKeyboardButton("🏦 UPI", callback_data="dep_meth_UPI")],
            [InlineKeyboardButton("🛍️ Amazon Gift Card", callback_data="dep_meth_Amazon")],
            PremiumUI.cancel_inline()
        ])

    @staticmethod
    def crypto_selection() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("USDT (BEP20)", callback_data="crypto_USDT"), InlineKeyboardButton("BTC", callback_data="crypto_BTC")],
            [InlineKeyboardButton("ETH", callback_data="crypto_ETH"), InlineKeyboardButton("SOL", callback_data="crypto_SOL")],
            PremiumUI.cancel_inline()
        ])

    @staticmethod
    def buy_currency_selection(group_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇳 Pay in INR", callback_data=f"buy_curr_INR_{group_id}"), InlineKeyboardButton("🇺🇸 Pay in USD", callback_data=f"buy_curr_USD_{group_id}")],
            PremiumUI.cancel_inline()
        ])

    @staticmethod
    def buy_payment_methods(group_id: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 Crypto", callback_data=f"buy_meth_Crypto_{group_id}"), InlineKeyboardButton("⭐ Telegram Stars", callback_data=f"buy_meth_Stars_{group_id}")],
            [InlineKeyboardButton("🛍️ Amazon Gift Card", callback_data=f"buy_meth_Amazon_{group_id}")],
            PremiumUI.cancel_inline()
        ])

    @staticmethod
    def group_list() -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(f"{v['name']} - ₹{v['price']} | ${v['usd_price']}", callback_data=f"buy_sel_{k}")] for k, v in GROUPS.items()]
        keyboard.append(PremiumUI.cancel_inline())
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def demo_list() -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(f"🎬 {v['name']} Demo", url=v['demo'])] for k, v in GROUPS.items() if v.get('demo')]
        return InlineKeyboardMarkup(keyboard)
        
