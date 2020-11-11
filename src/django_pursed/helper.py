#!/usr/bin/env python3

"""
This program does some actions that `manage` does not. Possible commands:

    create_fake_users
        creates some fake users, to interact with the Django site

    deposit [user] [amount]

Use `command` --help for command specific options.
"""

import os, sys, argparse, json


def deposit(username, amount):
    from django.db.utils import IntegrityError
    from django.db import transaction
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission
    import django.contrib.auth as A
    #
    from wallet.utils import  get_wallet_or_create
    from wallet.models import Wallet
    content_type = ContentType.objects.get_for_model(Wallet)
    #
    UsMo = A.get_user_model()
    user = UsMo.objects.filter(username=username).get()
    wallet = get_wallet_or_create(user)
    with transaction.atomic():
        wallet.deposit(value=float(amount),description='deposit from command line')


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
    from wallet.models import Wallet
    content_type = ContentType.objects.get_for_model(Wallet)
    #
    UsMo = A.get_user_model()
    for U,P in ('foobar', 'barfoo'), ('jsmith',"123456"), :
        E=_build_fake_email(U)
        print('*** creating user %r password %r with "operate" permission' % (U,P))
        try:
            UsMo.objects.create_user(U,email=E,password=P).save()
        except IntegrityError:
            pass
        except Exception as e:
            print('Cannot create user %r : %r' %(U,e))
        #
        user = UsMo.objects.filter(username=U).get()
        permission = Permission.objects.get(content_type = content_type,
                                            codename='operate')
        user.user_permissions.add(permission)
        permission = Permission.objects.get(content_type = content_type,
                                            codename='view_wallet')
        user.user_permissions.add(permission)

    #
    for U,P in ("caesar",  "julius"), :
        print('*** creating superuser %r password %r' % (U,P))
        E=_build_fake_email(U)
        try:
            UsMo.objects.create_superuser(U,email=E,password=P).save()
        except IntegrityError:
            pass
        except Exception as e:
            print('Cannot create user %r  : %r' %(U,e))
    return True


def main(argv):
    #
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', help='specific command',nargs='+')
    args = parser.parse_args()
    argv = args.command
    #
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_pursed.settings')
    import django
    django.setup()
    if argv[0] == 'create_fake_users':
        return create_fake_users()
    elif argv[0] == 'deposit':
        return deposit(argv[1],argv[2])
    else:
        sys.stderr.write("command not recognized : %r\n" % (argv,))
        sys.stderr.write(__doc__%{'arg0':sys.argv[0]})
        return False

if __name__ == '__main__':
    ret = main(sys.argv)
    sys.exit(0 if ret else 13)
