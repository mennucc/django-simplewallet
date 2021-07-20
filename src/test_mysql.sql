CREATE USER 'django_wallet_user'@'%' IDENTIFIED WITH mysql_native_password BY '603a7cdc47f0f963';

CREATE DATABASE django_wallet CHARACTER SET utf8;
GRANT ALL ON django_wallet.* TO 'django_wallet_user'@'%';

CREATE DATABASE test_django_wallet CHARACTER SET utf8;
GRANT ALL ON test_django_wallet.* TO 'django_wallet_user'@'%';

FLUSH PRIVILEGES;
