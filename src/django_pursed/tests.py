import logging
logger = logging.getLogger(__name__)


from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TransactionTestCase

from wallet.errors import InsufficientBalance
from wallet.models import Wallet
from wallet.utils import get_wallet_or_create

# Create your tests here.


class UsersTestCase(TransactionTestCase):
    def setUp(self):
        logger.info('Creating users...')
        from helper import create_fake_users
        self.users = create_fake_users()

class OperationsTestCase(UsersTestCase):
    
    def test_operations_arguments(self):
        from wallet.utils import deposit, transfer, withdraw
        R = transfer(amount=14)
        self.assertEqual(R, False)
        R = deposit(amount=14)
        self.assertEqual(R, False)
        R = withdraw(amount=14)
        self.assertEqual(R, False)
        
    def test_operations(self):
        """Test the basic wallet withdraw operation on a
        wallet that has an initial balance."""
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


