from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    TEMP_ENABLED: bool = Field(False, description="Set to true to enable the temperature service.")
    DATABASE_URL: str = Field(..., env='DATABASE_URL')
    SERVICE_TOKEN: str = Field(..., description="The static token for authenticating service-to-service requests.")
    W1_GPIO_PIN: int = Field(4, description="The GPIO pin for the 1-wire bus.")
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8001
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ALLOWED_HOSTS: list[str] = ["*"]

    class Config:
        env_file = 'temp/.env'
        env_file_encoding = 'utf-8'

settings = Settings()