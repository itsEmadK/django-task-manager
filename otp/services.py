from django.core.mail import send_mail

from otp.models import OTP


class OTPServices:

    @staticmethod
    def request_otp(email):
        otp, otp_code = OTP.objects.generate()

        send_mail(
            subject="Task Manager one time code",
            message=f"here is your code: {otp_code}",
            from_email="info@taskmgr.com",
            recipient_list=[email],
        )

        return otp.challenge_id
