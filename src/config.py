from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
import os

class Settings(BaseSettings):
    bot_token: SecretStr
    owner_id: int
    owner_username: str
    main_channel: str
    demo_channel: str
    database_url: str
    
    btc_address: str = "Not Configured"
    eth_address: str = "Not Configured"
    sol_address: str = "Not Configured"
    usdt_address: str = "Not Configured"
    stars_provider_token: str = ""
    usd_to_inr_rate: float = 85.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
