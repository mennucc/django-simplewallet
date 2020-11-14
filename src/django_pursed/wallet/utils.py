
import sys, os, http, pickle, base64, copy, re

import logging
logger = logging.getLogger(__name__)

from django.core.exceptions import SuspiciousOperation
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, QueryDict
from django.db import models, transaction
from django import forms
from django.core import signing

from .models import Wallet, Transaction


def encode_purchase(purchase_amount, description, pickled_function, redirect_ok, redirect_fails):
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

def _wallet_helper_(functor, username=None, email=None, group=None):
    from django.db.utils import IntegrityError
    from django.db import transaction
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission, Group
    import django.contrib.auth as A
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
    UsMo = A.get_user_model()
    #
    if username or email:
        O = UsMo.objects
        if username: O=O.filter(username=username)
        if email: O=O.filter(email=email)
        user = O.get()
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


def deposit(amount, username=None, email=None, group=None):
    "deposit `amount` to either an user (identified by `username` or `email`), or all users in a group"
    def functor(wallet, *v, **k):
        return wallet.deposit(value=amount, description='deposit from command line', *v, **k)
    return _wallet_helper_(functor, username=username, email=email, group=group)

