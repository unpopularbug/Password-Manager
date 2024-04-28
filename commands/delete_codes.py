from django.core.management.base import BaseCommand
from App.models import PasswordResetCode, VerificationCode
from celery import shared_task


#pylint: disable=no-member
class Command(BaseCommand):
    help = 'Deletes expired password reset & verification codes'

    def handle(self, *args, **options):
        delete_expired_codes.apply_async(countdown=300)
        self.stdout.write(self.style.SUCCESS('Code deletion task scheduled successfully.'))


@shared_task
def delete_expired_codes():
    VerificationCode.delete_expired_codes()
    PasswordResetCode.delete_expired_codes()