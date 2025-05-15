from pydantic import BaseSettings

class Settings(BaseSettings):
    app_name: str = "MyApp"
    database_url: str = "sqlite:///./test.db"
    secret_key: str = "supersecret"

    class Config:
        env_file = ".env"

settings = Settings()
