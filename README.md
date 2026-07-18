# Premium Telegram Payment Bot

## Environment Setup
Store your crypto wallet addresses directly in Railway Variables using the keys:
`USDT_ADDRESS`, `BTC_ADDRESS`, `ETH_ADDRESS`, `SOL_ADDRESS`.
No need to edit the source code to change addresses.

## Group Configuration
Open `src/groups_config.py` to add, edit, or remove your private groups. 
The bot reads this file instantly.

## Automatic Invite Links
When a user pays via Telegram Stars (or when Admin approves an Amazon/Crypto/UPI payment), the bot uses `member_limit=1` to generate a secure, 1-time-use invite link via the API and sends it securely to the user's DM. **You must add the bot as an Administrator in your private groups with the "Invite Users via Link" permission.**

## Admin Broadcast & Wallet System
- Send `/broadcast` -> Then send any text, photo, video, or document. It natively copies exact formatting/spoilers.
- Send `/addbalance <user_id> <amount>` -> To manual credit.
- Send `/removebalance <user_id> <amount>` -> To manual deduct.
- 
