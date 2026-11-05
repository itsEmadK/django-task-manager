from django.core import exceptions
from django.db import models
from django.utils import timezone

from accounts.models import User


def validate_due_date_in_the_future(value):
    if value < timezone.now():
        raise exceptions.ValidationError("Due date must be in the future")


class Category(models.Model):
    name = models.CharField(max_length=150, blank=False)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories",
        related_query_name="category",
        blank=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Task(models.Model):

    class Priority(models.IntegerChoices):
        NONE = 0, "None"
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"
        URGENT = 4, "Urgent"

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        DOING = "doing", "Doing"
        DONE = "done", "Done"

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        related_query_name="task",
        blank=False,
    )
    title = models.CharField(
        max_length=150,
        blank=False,
    )
    notes = models.TextField(blank=True)
    due_date = models.DateTimeField(
        blank=True,
        validators=[validate_due_date_in_the_future],
    )
    priority = models.IntegerField(
        choices=Priority,
        default=Priority.NONE,
    )
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.NOT_STARTED,
    )
    prerequisites = models.ManyToManyField(
        to="self",
        symmetrical=False,
        blank=True,
        related_name="dependents",
        related_query_name="dependent",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="tasks",
        related_query_name="task",
    )

    def clean(self):
        super().clean()
        if self.prerequisites.filter(id=self.id).exists():
            raise exceptions.ValidationError("task can't be a prerequisite of itself")
