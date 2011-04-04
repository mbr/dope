DEBUG = True
SECRET_KEY = 'devkey'
FILE_STORAGE = './files'
SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
SQLALCHEMY_ECHO = DEBUG
RANDOM_BYTES_PER_ID = 8
HASHFUNC = 'sha256'
FCGI_SOCKET = './dope.sock'
OPENID_FS_STORE_PATH = './openid'
PLUPLOAD_RUNTIMES = ['html5','html4']
FORCE_DOWNLOAD = False
SMART_FILENAME_REDIRECT = True

# use PERMANENT_SESSION_LIFETIME to set the time, default 31 days
PERSIST_SESSION = True