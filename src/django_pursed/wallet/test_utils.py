from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .models import Wallet

import logging


User = get_user_model()

logger = logging.getLogger(__name__)


class WalletTestCase(TransactionTestCase):

    def _create_initial_balance(self, value):
        self.wallet.transaction_set.create(
            value=value,
            running_balance=value
        )
        self.wallet.current_balance = value
        self.wallet.save()

    def setUp(self):
        logger.info('Creating wallet...')
        self.user = User()
        self.user.save()
        self.wallet = self.user.wallet_set.create()
        self.wallet.save()
        logger.info('Wallet created.')

        content_type = ContentType.objects.get_for_model(Wallet)
        permission = Permission.objects.get(content_type = content_type,
                                            codename='operate')
        self.user.user_permissions.add(permission)
