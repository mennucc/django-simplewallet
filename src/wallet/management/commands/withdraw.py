# https://docs.djangoproject.com/en/3.2/howto/custom-management-commands/
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('--amount',type=float,required=True,\
                            help='amount')
        parser.add_argument('--description',type=str,\
                            help='description of the operation')
        parser.add_argument('--from-username',type=str,\
                            help='username to withdraw from')
        parser.add_argument('--from-email',type=str,\
                            help='email of user to withdraw from')


    def handle(self, *args, **options):
        from wallet import utils
        utils.withdraw(options.get('amount'), from_username=options.get('from_username'),
                       from_email=options.get('from_email'), description=options.get('description'))
