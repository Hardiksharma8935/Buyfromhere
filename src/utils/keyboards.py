from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

class PremiumUI:
    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton("💰 Deposit"), KeyboardButton("🛒 Purchase")],
            [KeyboardButton("👤 Profile"), KeyboardButton("👛 Wallet")],
            [KeyboardButton("🎁 Referral"), KeyboardButton("📜 History")],
            [KeyboardButton("📢 Channel"), KeyboardButton("🎧 Support")]
        ]
        # Changed 'persistent' to 'is_persistent'
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

    @staticmethod
    def back_button(callback_data: str = "main_menu") -> list:
        return [InlineKeyboardButton("🔙 Back", callback_data=callback_data)]

    @staticmethod
    def cancel_inline() -> list:
        return [InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]

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
            [InlineKeyboardButton("🪙 Crypto", callback_data="dep_meth_Crypto")],
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
        
