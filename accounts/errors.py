from rest_framework import status
from rest_framework.exceptions import APIException


class ProfileAlreadyExists(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "you already have a profile"
    default_code = "profile_already_exists"
