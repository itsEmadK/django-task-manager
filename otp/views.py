from drf_spectacular.utils import extend_schema
from knox.models import AuthToken
from rest_framework.response import Response
from rest_framework.views import APIView

from otp.serializers import (
    VerifyEmailOTPRequestSerializer,
    VerifyEmailOTPResponseSerializer,
)


class VerifyEmailOTPView(APIView):

    @extend_schema(
        request=VerifyEmailOTPRequestSerializer,
        responses=[VerifyEmailOTPResponseSerializer],
    )
    def post(self, request):
        request_serializer = VerifyEmailOTPRequestSerializer(
            data=request.data,
        )

        request_serializer.is_valid(raise_exception=True)
        otp = request_serializer.save()
        user = otp.user
        user.email_verified = True
        token, token_key = AuthToken.objects.create(user=user)  # type: ignore

        response_serializer = VerifyEmailOTPResponseSerializer(
            instance={
                "user": user,
                "token": token_key,
                "expiry": token.expiry,
            },
        )

        return Response(response_serializer.data)
