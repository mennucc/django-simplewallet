"""
Django settings for django_pursed project.

Generated by 'django-admin startproject' using Django 1.9.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os, sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'tqak%@-xh1*p!2vj$v!-k0mt+1$&k76_g_mh$&317o*4kf+vz9'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'wallet',
    'django_pursed',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'django_pursed.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'django_pursed/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'django_pursed.wsgi.application'

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

if 'DOCKER_DATABASE_URL' in os.environ:
    # this is used inside the docker instance
    import dj_database_url
    D = dj_database_url.parse(os.environ['DOCKER_DATABASE_URL'])
    V = int(os.environ.get('DOCKER_DATABASE_VERSION','5'))
    if V > 5:
        ## if you prefer to use the connector
        # https://dev.mysql.com/doc/connector-python/en/
        O=D.get('OPTIONS',{})
        O['auth_plugin'] = 'mysql_native_password'
        D['ENGINE'] = 'mysql.connector.django'
    DATABASES = {
        'default': D
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR,'var/sqlite_database'),
        }
    }



if False:
    # This part is to set up this app in an existing MySQL. You may want to read
    #  https://www.digitalocean.com/community/tutorials/how-to-create-a-django-app-and-connect-it-to-a-database
    # to understand how to setup mysql for django;
    # but look at 'test_mysql.sql' for the exact list of commands to insert into mysql for this to work
    #
    a = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]),'test_mysql.cnf'))
    assert os.path.isfile(a),a
    #
    ## https://docs.djangoproject.com/en/dev/ref/databases/#mysql-notes
    ## older MySQL may prefer this, that is the Django recommended choice
    D = {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': { 'read_default_file': a, },
          # idea from  https://stackoverflow.com/a/45131868/5058564
        'TEST': { 'NAME': 'test_django_wallet', },
        }
    if False:
        # recent MySQL, such as MySQL 8, prefer this
        D['auth_plugin'] = 'mysql_native_password'
        D['OPTIONS']['auth_plugin'] = 'mysql_native_password'
        D['ENGINE'] = 'mysql.connector.django'
    DATABASES = {
        'default': D,
    }

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR,'www/static')

#### django_pursed specific settings

## field for storing value
# WALLET_CURRENCY_STORE_FIELD = models.BigIntegerField

## name of currency
# WALLET_CURRENCY_NAME = 'coins'

### Name, or icon, of currency, as an html snippet, possibly with a link to further explanations.
## The default is set to the "generic currency" unicode symbol, see https://en.wikipedia.org/wiki/Currency_sign_(typography)
# WALLET_CURRENCY_ICON = '&#164;'
## Example using bootstrap, see https://getbootstrap.com/docs/4.0/components/tooltips/ for more info
## (if you want to test this, the javascript is already activated at the end of the `base.html` template)
# WALLET_CURRENCY_ICON =  """<span data-toggle="tooltip" data-placement="top" title="coins">&#164;</span>"""

## if utils.get_wallet_or_create() will create a wallet for the user when the user hasn't it
# WALLET_CREATE_WALLET = True
