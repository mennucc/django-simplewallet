import logging
logger = logging.getLogger(__name__)

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .test_utils import WalletTestCase
from .errors import InsufficientBalance
from .models import Wallet
from .utils import get_wallet_or_create

# Create your tests here.


class BalanceTestCase(WalletTestCase):

    def test_default_balance(self):
        self.assertEqual(self.wallet.current_balance, 0)


class DepositTestCase(WalletTestCase):
    
    def test_deposit(self):
        """Test the basic wallet deposit operation."""
        DEPOSIT = 100
        DESCRIPTION = 'First deposit'
        T = self.wallet.deposit(DEPOSIT, description=DESCRIPTION)

        # The wallet's current_balance should also reflect
        # the deposit's value.
        self.assertEqual(self.wallet.current_balance, DEPOSIT)

        # When I create a deposit, the wallet should create
        # a transaction equal to the value of the deposit.
        self.assertEqual(self.wallet.transaction_set.first().value, DEPOSIT)

        self.assertEqual(DESCRIPTION, T.description)


class WithdrawTestCase(WalletTestCase):

    def test_withdraw(self):
        "Test the basic wallet withdraw operation on a wallet that has an initial balance."
        INITIAL_BALANCE = 100
        self._create_initial_balance(INITIAL_BALANCE)

        WITHDRAW = 99
        self.wallet.withdraw(WITHDRAW)

        # Test that the wallet's current_balance that it
        # matches the wallet's initial balance - the
        # withdrawn amount.
        self.assertEqual(self.wallet.current_balance,
                INITIAL_BALANCE - WITHDRAW)

        # When a withdraw transaction succeeds, a
        # transaction will be created and it's value should
        # match the withdrawn value (as negative).
        self.assertEqual(self.wallet.transaction_set.last().value, -WITHDRAW)

    def test_no_balance_withdraw(self):
        "Test the basic wallet withdraw operation on a  wallet without any transaction."
        with self.assertRaises(InsufficientBalance):
            self.wallet.withdraw(100)


class TransferTestCase(WalletTestCase):

    def test_transfer(self):
        """Test the basic tranfer operation on a wallet."""
        INITIAL_BALANCE = 100
        TRANSFER_AMOUNT = 100
        self._create_initial_balance(INITIAL_BALANCE)

        # We create a second wallet.
        wallet2 = self.user.wallet_set.create()

        # And now, we transfer all the balance the first
        # wallet has.
        T1, T2 = self.wallet.transfer(wallet2, TRANSFER_AMOUNT)

        # We check that the first wallet has its balance
        self.assertEqual(self.wallet.current_balance,
                INITIAL_BALANCE - TRANSFER_AMOUNT)

        # We also check that the second wallet has the
        # transferred balance.
        self.assertEqual(wallet2.current_balance, TRANSFER_AMOUNT)

        self.assertEqual(T2.related_object, self.wallet)
        self.assertEqual(wallet2, T1.related_object)

    def test_transfer_insufficient_balance(self):
        """Test a scenario where a transfer is done on a
        wallet with an insufficient balance."""
        INITIAL_BALANCE = 100
        TRANSFER_AMOUNT = 150
        self._create_initial_balance(INITIAL_BALANCE)

        # We create a second wallet.
        wallet2 = self.user.wallet_set.create()

        with self.assertRaises(InsufficientBalance):
            self.wallet.transfer(wallet2, TRANSFER_AMOUNT)


class PermissionTestCase(WalletTestCase):

    def test_no_permission(self):

        content_type = ContentType.objects.get_for_model(Wallet)
        permission = Permission.objects.get(content_type = content_type,
                                            codename='operate')

        self.user.user_permissions.remove(permission)

        with self.assertRaises(PermissionDenied):
            self.wallet.deposit(100)

from django.test import TransactionTestCase

class UsersTestCase(TransactionTestCase):
    def setUp(self):
        logger.info('Creating users...')
        from helper import create_fake_users
        self.users = create_fake_users()

class OperationsTestCase(UsersTestCase):
    
    def test_operations_arguments(self):
        from wallet.utils import deposit, transfer, withdraw
        with self.assertLogs() as cm:
            R = transfer(amount=14)
        self.assertEqual(R, False)
        with self.assertLogs() as cm:
            R = deposit(amount=14)
        self.assertEqual(R, False)
        with self.assertLogs() as cm:
            R = withdraw(amount=14)
        self.assertEqual(R, False)
        
    def test_operations(self):
        "Test the basic wallet withdraw operation on a wallet that has an initial balance."
        from wallet.utils import deposit, transfer, withdraw
        #
        logger.info('Deposit to foobar')
        deposit(amount=100, username='foobar')
        wallet = get_wallet_or_create('foobar')
        self.assertEqual(100, wallet.current_balance)
        #
        logger.info('Transfer from foobar to jsmith')
        transfer(amount=33, from_username='foobar', username='jsmith')
        #
        wallet = get_wallet_or_create('foobar')
        self.assertEqual(wallet.current_balance, 67)
        wallet = get_wallet_or_create('jsmith')
        self.assertEqual(wallet.current_balance, 33)
        #
        logger.info('Withdraw from foobar')
        withdraw(amount=7, from_username='foobar')
        wallet = get_wallet_or_create('foobar')
        self.assertEqual(wallet.current_balance, 60)
        #
        logger.info('Transfer from foobar to rjoe, permission denied')
        with self.assertRaises(PermissionDenied):
            transfer(amount=14, from_username='foobar', username='rjoe')
        # nothing should have been withdrawn
        wallet = get_wallet_or_create('foobar')
        self.assertEqual(wallet.current_balance, 60)


