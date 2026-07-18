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
            [InlineKeyboardButton("⭐ Telegram Stars", callback_data="dep_meth_Stars")],
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
    def buy_currency_selection(group_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🇮🇳 Pay in INR", callback_data=f"buy_curr_INR_{group_id}"), InlineKeyboardButton("🇺🇸 Pay in USD", callback_data=f"buy_curr_USD_{group_id}")],
            PremiumUI.cancel_inline()
        ])

    @staticmethod
    def buy_payment_methods(group_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🪙 Crypto", callback_data=f"buy_meth_Crypto_{group_id}")],
            [InlineKeyboardButton("🛍️ Amazon Gift Card", callback_data=f"buy_meth_Amazon_{group_id}")],
            [InlineKeyboardButton("⭐ Telegram Stars", callback_data=f"buy_meth_Stars_{group_id}")],
            PremiumUI.cancel_inline()
        ])

    # --- ADMIN KEYBOARDS ---
    @staticmethod
    def admin_main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📦 Manage Groups", callback_data="admin_groups"), InlineKeyboardButton("🎬 Manage Demos", callback_data="admin_demos")],
            [InlineKeyboardButton("⚙️ Settings & Links", callback_data="admin_settings")],
            [InlineKeyboardButton("❌ Close Panel", callback_data="cancel_action")]
        ])

    @staticmethod
    def admin_settings_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Main Channel Link", callback_data="admin_set_MAIN_CHANNEL_LINK")],
            [InlineKeyboardButton("🪙 USDT Address", callback_data="admin_set_USDT_ADDRESS"), InlineKeyboardButton("🪙 BTC Address", callback_data="admin_set_BTC_ADDRESS")],
            [InlineKeyboardButton("🪙 ETH Address", callback_data="admin_set_ETH_ADDRESS"), InlineKeyboardButton("🪙 SOL Address", callback_data="admin_set_SOL_ADDRESS")],
            [InlineKeyboardButton("🔙 Back to Admin", callback_data="admin_home")]
        ])
        
