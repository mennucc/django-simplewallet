#!/usr/bin/env python3

"""
This program does some actions that `manage` does not. Possible commands:

    create_fake_users
        creates some fake users, to interact with the Django site

    deposit [--username username] [--email email] [--group group] [--amount amount]
        deposit `amount` to either an user (identified by `username` or `email`), or all users in a group

    ping
        check if database is up and running

Use `command` --help for command specific options.
"""

import os, sys, argparse, json

import logging
logger = logging.getLogger('helper')


## from https://github.com/mozilla-services/python-dockerflow/blob/master/src/dockerflow/django/checks.py
def check_database_connected():
    """
    A Django check to see if connecting to the configured default
    database backend succeeds.
    """

    from django.core.exceptions import ImproperlyConfigured
    from django.db import connection
    from django.db.utils import OperationalError, ProgrammingError

    msg = None

    try:
        connection.ensure_connection()
    except OperationalError as e:
        msg = "Could not connect to database: {!s}".format(e)
    except ImproperlyConfigured as e:
        msg = 'Datbase misconfigured: "{!s}"'.format(e)
    else:
        if not connection.is_usable():
            msg = "Database connection is not usable"

    return msg

def ping():
    from django.db import connection
    from django.db.utils import OperationalError
    # https://stackoverflow.com/a/32109155/5058564
    #db_conn = connections['default']
    msg = None
    try:
        msg = check_database_connected()
        connected = connection.ensure_connection()
    except Exception as e:
        msg = str(e)
    if msg is not None:
        print('Connection fails: '+str(msg))
    return msg is None


def _build_fake_email(e):
    from django.conf import settings
    import email
    a = settings.DEFAULT_FROM_EMAIL
    if not a or '@' not in a:
        return e + '@test.local'
    j = a.index('@')
    return a[:j] + '+' + e + a[j:]


def create_fake_users():
    from django.db.utils import IntegrityError
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission
    import django.contrib.auth as A
    #
    users_map = {}
    #
    UsMo = A.get_user_model()
    for U,P in ('foobar', 'barfoo'), ('jsmith',"123456"), :
        E=_build_fake_email(U)
        print('*** creating user %r password %r' % (U,P))
        try:
            user = UsMo.objects.create_user(U,email=E,password=P)
            user.save()
            users_map[U] = user
        except IntegrityError:
            pass
        except Exception as e:
            print('Cannot create user %r : %r' %(U,e))
        #
    from wallet.models import Wallet, Transaction
    wallet_content_type = ContentType.objects.get_for_model(Wallet)
    transaction_content_type = ContentType.objects.get_for_model(Transaction)
    for U in  'foobar', :
        user = UsMo.objects.filter(username=U).get()
        print('*** adding permissions to user %r: "operate", "view_wallet" and "view_transaction"' % (U,))
        permission = Permission.objects.get(content_type = wallet_content_type,
                                            codename='operate')
        user.user_permissions.add(permission)
        permission = Permission.objects.get(content_type = wallet_content_type,
                                            codename='view_wallet')
        user.user_permissions.add(permission)
        permission = Permission.objects.get(content_type = transaction_content_type,
                                            codename='view_transaction')
        user.user_permissions.add(permission)
    #
    for U,P in ("caesar",  "julius"), :
        print('*** creating superuser %r password %r' % (U,P))
        E=_build_fake_email(U)
        try:
            user = UsMo.objects.create_superuser(U,email=E,password=P)
            user.save()
            users_map[U] = user
        except IntegrityError:
            pass
        except Exception as e:
            print('Cannot create user %r  : %r' %(U,e))
    return users_map


def main(argv):
    #
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', help='specific command',nargs='+')
    #
    if 'deposit' in argv:
        parser.add_argument('--amount',type=float,required=True,\
                            help='amount to deposit')
        parser.add_argument('--username',type=str,\
                            help='username receiving the deposit')
        parser.add_argument('--email',type=str,\
                            help='email of user receiving the deposit')
        parser.add_argument('--group',type=str,\
                            help='group of users receiving the deposit')
    #
    args = parser.parse_args()
    argv = args.command
    #
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_pursed.settings')
    import django
    django.setup()
    if argv[0] == 'create_fake_users':
        return create_fake_users()
    elif argv[0] == 'ping':
        return ping()
    elif argv[0] == 'deposit':
        from wallet.utils import deposit
        return deposit(args.amount, username=args.username, email=args.email, group=args.group)
    else:
        sys.stderr.write("command not recognized : %r\n" % (argv,))
        sys.stderr.write(__doc__%{'arg0':sys.argv[0]})
        return False

if __name__ == '__main__':
    ret = main(sys.argv)
    sys.exit(0 if ret else 13)
