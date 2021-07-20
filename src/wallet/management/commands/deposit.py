# https://docs.djangoproject.com/en/3.2/howto/custom-management-commands/
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('--amount',type=float,required=True,\
                            help='amount')
        parser.add_argument('--description',type=str,\
                            help='description of the operation')
        parser.add_argument('--username',type=str,\
                            help='username receiving the deposit')
        parser.add_argument('--email',type=str,\
                            help='email of user receiving the deposit')
        parser.add_argument('--group',type=str,\
                            help='group of users receiving the deposit')

    def handle(self, *args, **options):
        from wallet import utils
        utils.deposit(options.get('amount'), username=options.get('username'),
                             email=options.get('email'), group=options.get('group'), description=options.get('description'))
