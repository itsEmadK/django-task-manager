import mimetypes

from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from tasks.models import Attachment


class ReadAttachmentSerializer(ModelSerializer):
    """Requires 'request' in the context to generate absolute file urls"""

    url = SerializerMethodField()
    file_size = SerializerMethodField()
    file_type = SerializerMethodField()
    file_name = SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id",
            "type",
            "url",
            "title",
            "notes",
            "order",
            "file_type",
            "file_size",
            "file_name",
        ]

    def get_url(self, obj):
        return obj.url or self.context["request"].build_absolute_uri(obj.file.url)

    def get_file_size(self, obj):
        if obj.file:
            return obj.file.size
        else:
            return None

    def get_file_type(self, obj):
        if obj.file:
            return mimetypes.guess_type(obj.file.name)[0]
        else:
            return None

    def get_file_name(self, obj):
        if obj.file:
            return obj.file.name
        else:
            return None

    def save(self):
        raise NotImplementedError("this serializer is read-only")


class WriteAttachmentSerializer(ModelSerializer):
    """Requires 'content_object' in serializer context"""

    class Meta:
        model = Attachment
        fields = [
            "type",
            "url",
            "file",
            "title",
            "notes",
            "order",
        ]
        extra_kwargs = {
            "file": {
                "required": False,
            },
            "url": {
                "required": False,
            },
        }

    def validate(self, attrs):
        type = attrs.get("type", None)
        file = attrs.get("file", None)
        url = attrs.get("url", None)

        if type == "file":
            if not file:
                raise ValidationError("file must be present for file attachments")
            if url:
                raise ValidationError("can't pass external url to a file attachment")
        elif type == "external_url":
            if not url:
                raise ValidationError(
                    "url must be present for external url attachments"
                )
            if file:
                raise ValidationError("can't pass file to an external url attachment")

        return attrs

    def save(self):
        content_object = self.context["content_object"]
        return super().save(content_object=content_object)
