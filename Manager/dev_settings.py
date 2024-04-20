import environ
import dj_database_url
from dotenv import load_dotenv
load_dotenv()

env = environ.Env()

environ.Env.read_env()

DEBUG = True

DATABASES = {
    'default': dj_database_url.parse(env('dev_DATABASE_URL'))
}