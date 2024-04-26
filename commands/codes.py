from django.core.management.base import BaseCommand
from App.models import PasswordResetCode

#pylint: disable=no-member
class Command(BaseCommand):
    help = 'Deletes expired password reset codes'

    def handle(self, *args, **options):
        PasswordResetCode.delete_expired_codes()
        self.stdout.write(self.style.SUCCESS('Expired password reset codes deleted successfully.'))