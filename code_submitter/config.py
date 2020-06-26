from starlette.config import Config

config = Config('.env')

DATABASE_URL: str = config('DATABASE_URL', default='sqlite:///sqlite.db')
TESTING: bool = config('TESTING', cast=bool, default=False)
