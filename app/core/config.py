from typing import Any

from pydantic import BaseModel, BaseSettings, PostgresDsn, root_validator


class AppConfig(BaseModel):
    workers: int = 4


class DB(BaseModel):
    host: str = 'localhost'
    port: str = '5432'
    username: str = 'username'
    password: str = 'password'
    name: str = 'name'
    url: str = ''

    @root_validator(pre=False)
    def assemble_dsn(cls, values: dict[str, Any]) -> dict[str, Any]:
        values['url'] = str(
            PostgresDsn.build(
                scheme='postgresql+asyncpg',
                username=values.get('username'),
                password=values.get('password'),
                host=values.get('host'),
                port=values.get('port'),
                path=f"/{values.get('name')}",
            )
        )
        return values


class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    db: DB = DB()

    class Config:
        env_file = '.env'
        case_sensitive = False
        env_nested_delimiter = '__'
        extra = 'allow'


settings = Settings()
