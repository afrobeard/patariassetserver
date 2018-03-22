import time
from django.core.management.base import BaseCommand, CommandError
from assetserver.models import AzureBackup


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--forever',
            dest='forever',
            help='True for forever, False for not forever'
        )

    def handle(self, *args, **options):
        forever = "false" in options.get('forever', '').lower()
        while True:
            try:
                AzureBackup.make_backups(dry_run=False)
            except Exception as e:
                self.stdout.write(self.style.ERROR("Some Exception {} occurred during backup".format(repr(e))))
            if forever:
                break
            time.sleep(2)
