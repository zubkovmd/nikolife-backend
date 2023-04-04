"""Service constants"""

# api token expire minutes
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 100
# group name for is_admin checks
ADMIN_GROUP_NAME = "admin"
# default user group name (sets this group for new users)
DEFAULT_USER_GROUP_NAME = "user"
# not authenticated user group
NOT_AUTHENTICATED_GROUP_NAME = "no_auth"
# max returned stories count
MAX_STORIES_COUNT = 10
# max returned stories count
MAX_ARTICLES_COUNT = 10
# superuser login for development (user will be created if 'development' set in ENVRIONMENT env variable)
DEV_SUPERUSER_LOGIN = "admin@mail.ru"
# superuser password for development.
# ATTENTION! PASSWORD SHOULD BE HASHED WITH CryptContext(schemes=["bcrypt"]).hash(PWD). Only then password can be pasted
# here. Also, you need change user password in postman (in postman password should not be crypted)
DEV_SUPERUSER_PASSWORD = "$2b$12$W6aPE5HGb8dcP1leBZhICOGw8kq095MzAffo5jCBM10YP1BPXVBZa"
