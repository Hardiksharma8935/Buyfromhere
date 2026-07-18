from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

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
        keyboard = [[InlineKeyboardButton("💰 Deposit to Wallet", callback_data="start_deposit_flow")]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def link_button(text: str, url: str) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text, url=url)]]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def currency_selection() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🇮🇳 INR (₹)", callback_data="dep_curr_INR"),
             InlineKeyboardButton("🇺🇸 USD ($)", callback_data="dep_curr_USD")],
            PremiumUI.cancel_inline()
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_methods() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🪙 Crypto", callback_data="dep_meth_Crypto"),
             InlineKeyboardButton("🏦 UPI", callback_data="dep_meth_UPI")],
            [InlineKeyboardButton("🛍️ Amazon Gift Card", callback_data="dep_meth_Amazon")],
            [InlineKeyboardButton("⭐ Telegram Stars", callback_data="dep_meth_Stars")],
            PremiumUI.cancel_inline()
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def crypto_selection() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("USDT (BEP20)", callback_data="crypto_USDT"),
             InlineKeyboardButton("BTC", callback_data="crypto_BTC")],
            [InlineKeyboardButton("ETH", callback_data="crypto_ETH"),
             InlineKeyboardButton("SOL", callback_data="crypto_SOL")],
            PremiumUI.cancel_inline()
        ]
        return InlineKeyboardMarkup(keyboard)
        
