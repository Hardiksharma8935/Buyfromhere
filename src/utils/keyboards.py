from telegram import InlineKeyboardButton, InlineKeyboardMarkup

class PremiumUI:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("💰 Deposit", callback_data="menu_deposit"), 
             InlineKeyboardButton("🛒 Purchase", callback_data="menu_purchase")],
            [InlineKeyboardButton("👤 Profile", callback_data="menu_profile"), 
             InlineKeyboardButton("💳 Wallet", callback_data="menu_wallet")],
            [InlineKeyboardButton("🎁 Referral", callback_data="menu_referral"), 
             InlineKeyboardButton("📜 History", callback_data="menu_history")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"), 
             InlineKeyboardButton("🎧 Support", url="https://t.me/your_support")]
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def back_button(callback_data: str = "main_menu") -> list:
        return [InlineKeyboardButton("🔙 Back", callback_data=callback_data)]

    @staticmethod
    def home_button() -> list:
        return [InlineKeyboardButton("🏠 Home", callback_data="main_menu")]

    @staticmethod
    def currency_selection() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🇮🇳 INR (₹)", callback_data="dep_curr_INR"),
             InlineKeyboardButton("🇺🇸 USD ($)", callback_data="dep_curr_USD")],
            PremiumUI.home_button()
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def payment_methods() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🪙 Crypto", callback_data="dep_meth_Crypto")],
            [InlineKeyboardButton("🛍️ Amazon Gift Card", callback_data="dep_meth_Amazon")],
            [InlineKeyboardButton("⭐ Telegram Stars", callback_data="dep_meth_Stars")],
            PremiumUI.back_button("menu_deposit")
        ]
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def crypto_selection() -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("USDT (BEP20)", callback_data="crypto_USDT"),
             InlineKeyboardButton("BTC", callback_data="crypto_BTC")],
            [InlineKeyboardButton("ETH", callback_data="crypto_ETH"),
             InlineKeyboardButton("SOL", callback_data="crypto_SOL")],
            PremiumUI.back_button("dep_meth_Crypto")
        ]
        return InlineKeyboardMarkup(keyboard)
      
