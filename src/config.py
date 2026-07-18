from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    bot_token: SecretStr
    owner_id: int
    owner_username: str
    database_url: str
    usd_to_inr_rate: float = 85.0
    main_channel_link: str = "https://t.me/NovaGenesisDev"

    # Crypto Wallets
    usdt_address: str = "Not Configured"
    btc_address: str = "Not Configured"
    eth_address: str = "Not Configured"
    sol_address: str = "Not Configured"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
