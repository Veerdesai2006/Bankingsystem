from pydantic_settings import BaseSettings, SettingsConfigDict
#Think of BaseSettings as a special version of a normal Python class that knows how to read environment variables.
#BaseSetting ->Please create an object whose values should come from environment variables
#SettingsConfigDict->This tells BaseSettings how it should behave.
class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )#->"Before reading environment variables, also load the .env file."
settings = Settings()  # type: ignore[call-arg]