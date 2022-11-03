"""Service constants"""

ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*100             # api token expire minutes
ADMIN_GROUP_NAME = "admin"                          # group name for is_admin checks
DEFAULT_USER_GROUP_NAME = "user"                    # default user group name (sets this group for new users)
MAX_STORIES_COUNT = 10                              # max returned stories count
MAX_ARTICLES_COUNT = 10                             # max returned stories count
DEV_SUPERUSER_LOGIN = "admin@mail.ru"               # superuser login for development (user will be created if 'development' set in ENVRIONMENT env variable)
# superuser password for development.
# ATTENTION! PASSWORD SHOULD BE HASHED WITH CryptContext(schemes=["bcrypt"]).hash(PWD). Only then password can be pasted
# here. Also, you need change user password in postman (in postman password should not be crypted)
DEV_SUPERUSER_PASSWORD = "$2b$12$W6aPE5HGb8dcP1leBZhICOGw8kq095MzAffo5jCBM10YP1BPXVBZa"
