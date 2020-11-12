from django.conf import settings
from django.db import models
from .errors import InsufficientBalance


# We'll be using BigIntegerField by default instead
# of DecimalField for simplicity. This can be configured
# though by setting `WALLET_CURRENCY_STORE_FIELD` in your
# `settings.py`.
CURRENCY_STORE_FIELD = getattr(settings,
        'WALLET_CURRENCY_STORE_FIELD', models.BigIntegerField)


class Wallet(models.Model):
    # We should reference to the AUTH_USER_MODEL so that
    # when this module is used and a different User is used,
    # this would still work out of the box.
    #
    # See 'Referencing the User model' [1]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # This stores the wallet's current balance. Also acts
    # like a cache to the wallet's balance as well.
    current_balance = CURRENCY_STORE_FIELD(default=0)

    # The date/time of the creation of this wallet.
    created_at = models.DateTimeField(auto_now_add=True)

    def deposit(self, value, description=''):
        """Deposits a value to the wallet.

        Also creates a new transaction with the deposit
        value.

        Returns the transaction.
        """
        T = self.transaction_set.create(
            value=value,
            running_balance=self.current_balance + value,
            description = description,
        )
        self.current_balance += value
        self.save()
        return T

    def withdraw(self, value, description=''):
        """Withdraw's a value from the wallet.

        Also creates a new transaction with the withdraw
        value.

        Should the withdrawn amount is greater than the
        balance this wallet currently has, it raises an
        :mod:`InsufficientBalance` error. This exception
        inherits from :mod:`django.db.IntegrityError`. So
        that it automatically rolls-back during a
        transaction lifecycle.

        Returns the transaction.
        """
        if value > self.current_balance:
            raise InsufficientBalance('This wallet has insufficient balance.')

        T = self.transaction_set.create(
            value=-value,
            running_balance=self.current_balance - value,
            description = description,
        )
        self.current_balance -= value
        self.save()
        return T

    def transfer(self, wallet, value, description=''):
        """Transfers an value to another wallet.
        Uses `deposit` and `withdraw` internally.

        Returns the two transactions, on the first and on the second wallet.
        """
        T1 = self.withdraw(value, description)
        T2 = wallet.deposit(value, description)
        return T1,T2


class Transaction(models.Model):
    # The wallet that holds this transaction.
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)

    # The value of this transaction.
    value = CURRENCY_STORE_FIELD(default=0)

    # The value of the wallet at the time of this
    # transaction. Useful for displaying transaction
    # history.
    running_balance = CURRENCY_STORE_FIELD(default=0)

    # The date/time of the creation of this transaction.
    created_at = models.DateTimeField(auto_now_add=True)
    
    # The description of the transaction
    description = models.CharField(max_length=300, blank=True)


# Footnotes
# [1]: https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#referencing-the-user-model
