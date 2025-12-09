from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class LocalSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")


class PostgresConfig(LocalSettings):
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    user: str = Field(default="postgres", alias="POSTGRES_USER")
    password: str = Field(default="pgAdminPassword", alias="POSTGRES_PASSWORD")
    db: str = Field(default="mixtura-auth", alias="POSTGRES_DB")

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisConfig(LocalSettings):
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    user: str = Field(default="default", alias="REDIS_USER")
    password: str = Field(default="", alias="REDIS_PASSWORD")

    @property
    def url(self) -> str:
        return f"redis://{self.user}:{self.password}@{self.host}:{self.port}"


class ServerConfig(LocalSettings):
    host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    port: int = Field(default=8000, alias="SERVER_PORT")


class RabbitConfig(LocalSettings):
    host: str = Field(default="localhost", alias="RABBITMQ_HOST")
    port: int = Field(default=5672, alias="RABBITMQ_PORT")
    user: str = Field(default="guest", alias="RABBITMQ_USER")
    password: str = Field(default="guest", alias="RABBITMQ_PASSWORD")
    vhost: str = Field(default="/", alias="RABBITMQ_VHOST")

    @property
    def url(self) -> str:
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}{self.vhost}"


class Env(LocalSettings):
    server: ServerConfig = Field(default_factory=ServerConfig)  # type: ignore
    redis: RedisConfig = Field(default_factory=RedisConfig)  # type: ignore
    rabbit: RabbitConfig = Field(default_factory=RabbitConfig)  # type: ignore
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)  # type: ignore

    @classmethod
    def load(cls) -> "Env":
        return cls()


env = Env.load()
