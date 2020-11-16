
import sys, os, http, pickle, base64, copy, re

import logging
logger = logging.getLogger(__name__)

from django.core.exceptions import SuspiciousOperation
import django.contrib.auth as django_auth
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, QueryDict
from django.db import models, transaction
from django import forms
from django.core import signing

def encode_buying_function(function):
    return base64.b64encode(pickle.dumps(function)).decode()

def encode_purchase(purchase_amount, description, pickled_function, redirect_ok, redirect_fails):
    if isinstance(purchase_amount, (int,float)):
        purchase_amount = str(purchase_amount)
    assert isinstance(purchase_amount,str)
    assert isinstance(description,str)
    assert isinstance(pickled_function,str)
    assert isinstance(redirect_ok,str)
    assert isinstance(redirect_fails,str)
    # convert to UNIX line ending
    description = re.sub("\r\n", '\n', description)
    #
    return signing.dumps([purchase_amount, description, pickled_function, redirect_ok, redirect_fails])

def purchase_as_dict(purchase_amount, description, pickled_function, redirect_ok, redirect_fails):
    # convert to UNIX line ending
    description = re.sub("\r\n", '\n', description)
    #
    D = {
        'purchase_amount': purchase_amount,
        'description' : description,
        'pickled_function' : pickled_function,  
        'redirect_ok': redirect_ok, 
        'redirect_fails': redirect_fails,
    }
    return D

def verify_purchase(form):
    encoded = form.cleaned_data['encoded']
    purchase_amount, description, pickled_function, redirect_ok, redirect_fails =  signing.loads(encoded)
    D = purchase_as_dict(purchase_amount, description, pickled_function, redirect_ok, redirect_fails)
    #
    O = copy.copy(form.cleaned_data)
    O.pop('encoded')
    # convert to UNIX line ending
    O['description'] = re.sub("\r\n", '\n', O['description'])
    #
    if D != O:
        logger.error('Purchase was altered encoded = %r != submitted = %r'%(D,O))
        raise SuspiciousOperation('Purchase was altered')
    return D

def get_wallet_or_create(user):
    from .models import Wallet, Transaction
    if isinstance(user, str):
        user = find_user(username=user)
    try:
        wallet = Wallet.objects.filter(user=user).get()
    except Wallet.DoesNotExist:
        if getattr(settings, 'WALLET_CREATE_WALLET', True):
            wallet = Wallet(user=user)
            wallet.save()
        else:
            raise
    return wallet


###################### wallet operation helper

def find_user(username=None, email=None):
    " find `User` matching `username` or `email` (or both, if both are given)"
    assert (username or email)
    UsMo = django_auth.get_user_model()
    if isinstance(username, UsMo):
        return username
    if isinstance(email, UsMo):
        return email
    O = UsMo.objects
    if username: O=O.filter(username=username)
    if email: O=O.filter(email=email)
    return O.get()

def _wallet_helper_(functor, username=None, email=None, group=None):
    from django.db.utils import IntegrityError
    from django.db import transaction
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission, Group
    from .models import Wallet, Transaction
    #
    if not (username or email or group):
        logger.warning('Please specify (--username or --email) or (--group)')
        return False
    if bool(username or email)  != bool(not group):
        # it actually works, but it is weird
        logger.warning('Please specify (--username or --email) or (--group) but not both')
        return False
    #
    content_type = ContentType.objects.get_for_model(Wallet)
    #
    if username or email:
        user = find_user(username=username, email=email)
        wallet = get_wallet_or_create(user)
        with transaction.atomic():
            functor(wallet)
    #
    if group:
        group = Group.objects.get(name=group)
        users = group.user_set.all()
        with transaction.atomic():
            for user in users:
                wallet = get_wallet_or_create(user)
                functor(wallet)
    return True


def deposit(amount, username=None, email=None, group=None, description=None):
    "deposit `amount` to either an user (identified by `username` or `email`), or all users in a group"
    #
    if description is None: description='deposit from command line'
    #
    def functor(wallet, *v, **k):
        return wallet.deposit(value=amount, description=description, *v, **k)
    return _wallet_helper_(functor, username=username, email=email, group=group)

def withdraw(amount, from_username=None, from_email=None, description=None):
    "withdraw `amount` from an user (identified by `username` or `from_email`)"
    #
    if description is None: description='withdraw from command line'
    #
    def functor(wallet, *v, **k):
        return wallet.withdraw(value=amount, description=description, *v, **k)
    return _wallet_helper_(functor, username=from_username, email=from_email)


def transfer(amount, from_username=None, from_email=None, username=None, email=None, group=None, description=None):
    """transfer `amount` , from an user (identified by `from_username` or `from_email`) , to
    either an user (identified by `username` or `email`), or all users in a group ; in this latter case
    `amount` will be transferred once for each user in the group """
    #
    if description is None: description='transfer from command line'
    #
    if not (from_username or from_email):
        logger.warning('Please specify (--from_username or --from_email)')
        return False
    #
    from_user   = find_user(username=from_username, email=from_email)
    from_wallet = get_wallet_or_create(from_user)
    #
    def functor(wallet, *v, **k):
        return from_wallet.transfer(wallet=wallet, value=amount, description=description, *v, **k)
    return _wallet_helper_(functor, username=username, email=email, group=group)
