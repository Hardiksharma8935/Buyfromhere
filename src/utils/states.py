from telegram.ext import ConversationHandler

# Deposit Flow States
CHOOSING_CURRENCY = 1
TYPING_AMOUNT = 2
CHOOSING_METHOD = 3
CHOOSING_CRYPTO = 4
UPLOADING_SCREENSHOT = 5

END = ConversationHandler.END
