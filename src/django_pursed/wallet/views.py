import sys, os, http, pickle, base64, copy

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

from .errors import StopPurchase

# We'll be using BigIntegerField by default instead
# of DecimalField for simplicity. This can be configured
# though by setting `WALLET_CURRENCY_STORE_FIELD` in your
# `settings.py`.
CURRENCY_STORE_FIELD = getattr(settings,
        'WALLET_CURRENCY_STORE_FIELD', models.BigIntegerField)

# you can specify a name for your currency
currency_name_ = getattr(settings, 'WALLET_CURRENCY_NAME', 'coins')

########################## forms

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['value', 'description']
    at_time = forms.CharField()

class PurchaseForm(forms.Form):
    purchase_amount = forms.CharField(help_text='Amount to be paid')
    description = forms.CharField(label='description',
                                  max_length=300,
                                  widget=forms.Textarea(attrs={'class': 'form-text w-100'}),
                                  help_text='Description of the purchase')
    pickled_function = forms.CharField(widget=forms.HiddenInput())
    redirect_ok = forms.CharField(widget=forms.HiddenInput())
    redirect_fails = forms.CharField(widget=forms.HiddenInput())
    encoded = forms.CharField(widget=forms.HiddenInput())


######################### utils

from .utils import *

################### views

def show(request):
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    if not request.user.has_perm('wallet.view_wallet'):
        return HttpResponse('No viewing permission', status=http.HTTPStatus.BAD_REQUEST)
    wallet = get_wallet_or_create(request.user)
    currency_name = currency_name_
    transactions = []
    if request.user.has_perm('wallet.view_transaction'):
        t = None
        for j in Transaction.objects.filter(wallet=wallet).order_by('-created_at').all():
            t=TransactionForm(instance=j,initial={'at_time': j.created_at.strftime("%Y-%m-%d %H:%M:%S") })
            transactions.append(t)
        transaction_template = TransactionForm()
        del t
    return render(request, 'show.html', locals() )

def authorize_purchase_url(request, encoded):
    if request.method == 'POST' :
        raise SuspiciousOperation('Is POST')
    if not request.user.has_perm('wallet.operate'):
        raise SuspiciousOperation('Cannot operate on wallet')
    currency_name = currency_name_
    wallet = get_wallet_or_create(request.user)
    purchase_amount, description, pickled_function, redirect_ok, redirect_fails =  signing.loads(encoded)
    D = purchase_as_dict(purchase_amount, description, pickled_function, redirect_ok, redirect_fails)
    D ['encoded'] = encoded
    purchaseform = PurchaseForm(D)
    for k in purchaseform.fields:
        purchaseform.fields[k].widget.attrs['readonly'] = True
    return render(request, 'authorize_purchase.html', locals() )


def authorize_purchase_post(request):
    if request.method != 'POST' :
        raise SuspiciousOperation('Is not POST')
    if not request.user.has_perm('wallet.operate'):
        raise SuspiciousOperation('Cannot operate on wallet')
    currency_name = currency_name_
    wallet = get_wallet_or_create(request.user)
    purchaseform = PurchaseForm(request.POST)
    if not purchaseform.is_valid():
        raise SuspiciousOperation('Invalid form')
    for k in purchaseform.fields:
        purchaseform.fields[k].widget.attrs['readonly'] = True
    return render(request, 'authorize_purchase.html', locals() )

def purchase(request):
    if request.method != 'POST' :
        raise SuspiciousOperation('Is not POST')
    if not request.user.has_perm('wallet.operate'):
        raise SuspiciousOperation('Cannot operate on wallet')
    currency_name = currency_name_
    purchaseform = PurchaseForm(request.POST)
    if not purchaseform.is_valid():
        raise SuspiciousOperation('Invalid form')
    try:
        V = verify_purchase(purchaseform)
    except SuspiciousOperation as e:
        logger.error('Hacking attempt META = %r',request.META)
        logger.error('Hacking attempt USER = %r',request.user)
        ret = '<a href="https://youtu.be/RfiQYRn7fBg">' + str(e) + '</a>'
        return HttpResponse(ret, status=http.HTTPStatus.BAD_REQUEST)
    #
    value = float(V['purchase_amount'])
    description = V['description']
    func = base64.b64decode(V['pickled_function'])
    func = pickle.loads(func)
    #
    wallet = get_wallet_or_create(request.user)
    #
    # https://docs.djangoproject.com/en/3.0/topics/db/transactions/
    try:
        with transaction.atomic():
            if value > wallet.current_balance:
                messages.add_message(request,messages.ERROR, 'This wallet has insufficient balance.')
                return redirect(V['redirect_fails'])
            z = func(request)
            ret = z.get('return_code')
            message = z.get('message','')
            related_object = z.get('related_object')
            if ret is True:
                wallet.withdraw(value=value, description=description, related_object=related_object)
    except StopPurchase as e:
        ret = str(e)
    except Exception as e:
        logger.exception('While running buying function : %r',e)
        ret = str(e)
    #
    if ret is True:
        messages.add_message(request,messages.INFO, "Purchase success: "+repr(V['description']))
        return redirect(V['redirect_ok'])
    else:
        messages.add_message(request,messages.ERROR, "Purchase failed: "+repr(ret))
        return redirect(V['redirect_fails'])

