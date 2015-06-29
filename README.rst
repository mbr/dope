Dope is a small WSGI application, that allows you to host files on a server
(similiar to services like Rapidshare, etc). At the moment, it simply scratches
my own itch and lacks features.


Notes
=====

If you use SQLite as your database backend, ensure that you use a version >
0.9.1 (note the strict greater than!), otherwise the connection pooling of
SQLAlchemy will mess up things a great deal (related commit:
http://github.com/mitsuhiko/flask-
sqlalchemy/commit/4d1a61e37dab85d15b1fc6a9a0b58f6041dfd942)
