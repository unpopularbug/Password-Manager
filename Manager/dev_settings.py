import os
from dotenv import load_dotenv
load_dotenv()


DEBUG = True


DATABASES = {
    'default': {
        'ENGINE': os.environ['db_engine'],
        'NAME': os.environ['db_name'],
        'USER': os.environ['db_user'],
        'PASSWORD': os.environ['db_password'],
        'HOST': os.environ['db_host'],
        'PORT': os.environ['db_port'],
        'OPTIONS': {'sslmode': 'require'},
    }
}