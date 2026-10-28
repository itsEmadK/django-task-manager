from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import RegisterRequestSerializer, RegisterResponseSerializer


class RegisterUser(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        request_serializer = RegisterRequestSerializer(
            data={
                "email": email,
                "password": password,
            },
        )
        request_serializer.is_valid(raise_exception=True)

        user, token = request_serializer.save()
        response_serializer = RegisterResponseSerializer(
            instance={"user": user, "token": token.key},
        )
        return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)
