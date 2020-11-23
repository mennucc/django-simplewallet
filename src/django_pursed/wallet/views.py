import sys, os, http, pickle, base64, copy, re

# taken from Django, for convenience
slug_re = re.compile(r'^[-a-zA-Z0-9_]+\Z')
number_re = re.compile(r'^[0-9]+\Z')

from django.contrib.auth.validators import UnicodeUsernameValidator

valid_user_re = UnicodeUsernameValidator().regex

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
from django.contrib.auth import get_user_model

UsMo = get_user_model()

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
        fields = ['value', 'running_balance', 'description']
    at_time = forms.CharField(help_text='Time of this transaction')
    related = forms.CharField(help_text='Object related to this transaction')

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
    " show wallet and transactions "
    currency_name = currency_name_
    #
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    if not request.user.has_perm('wallet.view_wallet'):
        return HttpResponse('No viewing permission', status=http.HTTPStatus.BAD_REQUEST)
    # GET
    nr = request.GET.get('nr')
    if not ( nr is None or number_re.match(nr) ) : return (HttpResponse('Bad "nr"', status=http.HTTPStatus.BAD_REQUEST))
    username = request.GET.get('username')
    if not ( username is None or valid_user_re.match(username) ) : return (HttpResponse('Bad "username"', status=http.HTTPStatus.BAD_REQUEST))
    # only staff can specify username
    if not request.user.is_staff:
        if username:
            logger.warning('User %s specified parameter username=%r :ignored ', request.user.username, username)
        username = None
    # set `thatuser`
    thatuser = None
    if username:
        try:
            thatuser = UsMo.objects.get(username=username)
        except UsMo.DoesNotExist:
            logger.warning('User %s specified parameter username=%r , non existent ', request.user.username, username)
            messages.add_message(request, messages.WARNING, '"username = %r" does not exist' % (username,))
            wallet = None
            transactions = []
            wallets = []
            thatuser = request.user
            return render(request, 'show.html', locals() )
    else:
        thatuser = request.user
    # at this point `thatuser` is set to something sensible
    #
    if nr is not None:
        # `nr` takes precedence
        try:
            wallet = Wallet.objects.get(id = nr)
        except Wallet.DoesNotExist:
            logger.warning('User %s specified parameter nr=%r , non existent ', request.user.username, nr)
            messages.add_message(request, messages.WARNING, '"id = %r" does not exist' % (nr,))
            wallet = None
            transactions = []
            wallets = list(Wallet.objects.filter(user=thatuser).all())
            return render(request, 'show.html', locals() )
        if wallet.user != thatuser:
            if request.user.is_staff:
                if username:
                    messages.add_message(request, messages.WARNING, '"username" ignored')
                thatuser = wallet.user
            else:
                # this happens when a regular user tries to access the wallet of someone else
                logger.warning('User %s specified wallet nr=%r owned by %r : ignored', request.user.username, nr, wallet.user.username)
                messages.add_message(request, messages.WARNING, '"nr" ignored')
                wallet = get_wallet_or_create(thatuser)
    else:
        wallet = get_wallet_or_create(thatuser)
    #
    del username, nr
    #
    whose =  ("%s's wallets" % thatuser) if (request.user.is_staff) else "Your wallets"
    whose_url = thatuser.get_absolute_url()
    wallets = list(Wallet.objects.filter(user=thatuser).all())
    #
    transactions = []
    if request.user.has_perm('wallet.view_transaction'):
        t = None
        for j in Transaction.objects.filter(wallet=wallet).order_by('-created_at').all():
            url = ''
            related = ''
            try:
                r = j.related_object
                if r is None:
                    related = ''
                elif isinstance(r, Wallet):
                    u = r.user
                    if j.value > 0 :
                        related = 'from user %s' % (u,)
                    else:
                        related = 'to user %s' % (u,)
                    url = u.get_absolute_url()
                else:
                    related = str(r)
                    if hasattr(r,'get_absolute_url'):
                        url = r.get_absolute_url()
            except Exception:
                logger.exception('While parsing related_object for %r', j)
            #if url:  related = ('<a href="%s">' % url) + related + '</a>'
            t=TransactionForm(instance=j,initial={'at_time': j.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                                                  'related' : related,
                                                  })
            # fixme this is not propagated to the template
            z = t.fields['related']
            z.widget.url = url
            #
            transactions.append(t)
        #
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

