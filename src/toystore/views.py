import pickle, base64

import logging
logger = logging.getLogger(__name__)

import django
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.urls.exceptions import NoReverseMatch, Resolver404
from django.conf import settings
from django import forms
from django.contrib import messages

from .models import BuyableObject

from wallet.errors import StopPurchase

# you can specify a name for your currency
currency_name_ = getattr(settings, 'WALLET_CURRENCY_NAME', 'coins')
# you can specify an icon, or other html, for your currency
currency_icon_ = getattr(settings, 'WALLET_CURRENCY_ICON', '&#164;')

buyable_objects = (('car',30),('doll',20),('ball',5),('train',40))


class ChooseForm(forms.Form):
    description = forms.CharField(label='description',
                                  max_length=300,
                                  help_text='Name of the object that you want to buy')

def index(request):
    if not request.user.is_authenticated:
        chooseform = buyables = None
    else:
        chooseform = ChooseForm()
        buyables = []
        for description,purchase_amount in buyable_objects:
            encoded, x = prepare_contract(description, purchase_amount, request.user)
            buyables.append((description, encoded))
    return render(request, 'index.html', locals())

class Buy(object):
    def __init__(self, buyable, user):
        self.user = user
        self.buyable = buyable
    #
    def check(self, *v,**k):
        if self.buyable.owners.filter(username=self.user.username).exists():
            raise StopPurchase( 'User %r already owns %r' % (self.user, self.buyable, ) )
    #
    def buy(self, *v,**k):
        self.check()
        self.buyable.owners.add(self.user)
        D = { 'return_code' : True,
              'related_object' : self.buyable ,
        }
        return D
    #
    def __call__(self, *v,**k):
        return self.buy(*v,**k)


def buy(request):
    " a simple view that accepts a form ChooseForm or a parameter, and starts a contract "
    if not request.user.is_authenticated:
        return redirect('%s?next=%s' % (settings.LOGIN_URL, request.path))
    #
    if request.method != 'POST' :
        description = request.GET.get('description','refrigerator')
    else:
        chooseform = ChooseForm(request.POST)
        if not chooseform.is_valid():
            raise SuspiciousOperation('Invalid form')
        description = chooseform.cleaned_data['description']
    #
    purchase_amount = '20'
    encoded, x = prepare_contract(description, purchase_amount, request.user)
    #
    redirect_ok = django.urls.reverse('bought')+'?result=ok'
    redirect_fails =  django.urls.reverse('bought')+'?result=fail'
    # checks that this object can be bought, just in case
    try:
        x.check()
    except StopPurchase as e:
        a = 'Purchase stopped : %r' % (e,)
        logger.warning(a)
        messages.add_message(request,messages.WARNING, a)
        return redirect(redirect_fails)
    except Exception as e:
        a = 'Purchase check failed : %r' % (e,)
        messages.add_message(request,messages.ERROR, a)
        logger.error(a)
        return redirect(redirect_fails)
    #
    return redirect(django.urls.reverse('wallet:authorize_purchase_url', kwargs={'encoded' : encoded}))

def prepare_contract(description, purchase_amount, user):
    " prepare an encoded contract to buy this object "
    try:
        buyable = BuyableObject.objects.filter(description = description).get()
    except BuyableObject.DoesNotExist:
        buyable = BuyableObject(description = description)
        buyable.save()
        logger.warning('Creating BuyableObject %r',buyable)
    #
    from wallet.views import encode_purchase, encode_buying_function
    #
    description = "buy an object\n of this kind:\n" + description
    #
    x = Buy(buyable=buyable, user=user)
    pickled_function = encode_buying_function(x)
    redirect_ok = django.urls.reverse('bought')+'?result=ok'
    redirect_fails =  django.urls.reverse('bought')+'?result=fail'
    encoded = encode_purchase(purchase_amount, description, pickled_function, redirect_ok, redirect_fails)
    #
    return encoded, x

def bought(request):
    result = request.GET.get('result')
    from wallet.utils import  get_wallet_or_create
    wallet = get_wallet_or_create(request.user)
    currency_name = currency_name_
    currency_icon = currency_icon_
    return render(request, 'bought.html', locals())
