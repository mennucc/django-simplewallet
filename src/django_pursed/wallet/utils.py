
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
