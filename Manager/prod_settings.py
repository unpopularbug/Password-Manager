import environ
from dotenv import load_dotenv
load_dotenv()


DEBUG = False


env = environ.Env()

environ.Env.read_env()

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///:memory:'),
}

DATABASES['default']['OPTIONS'] = {'sslmode': 'require'}