from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_env:str='development'
    database_url:str=''
    cors_origins_raw:str='http://localhost:3000'
    personal_api_key:str=''
    model_config=SettingsConfigDict(env_file='.env',extra='ignore')
    @property
    def cors_origins(self): return [x.strip() for x in self.cors_origins_raw.split(',') if x.strip()]
settings=Settings()
