from django.core import exceptions
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone

from accounts.models import User


class Priority(models.IntegerChoices):
    LOW = 1, "Low"
    MEDIUM = 2, "Medium"
    HIGH = 3, "High"
    URGENT = 4, "Urgent"


class Project(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        DOING = "doing", "Doing"
        PAUSED = "paused", "Paused"
        CANCELED = "canceled", "Canceled"
        DONE = "done", "Done"

    name = models.CharField(max_length=150)
    description = models.TextField(null=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects",
        related_query_name="project",
    )
    priority = models.IntegerField(
        choices=Priority,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.NOT_STARTED,
    )
    deadline = models.DateTimeField(null=True)

    @property
    def deadline_exceeded(self):
        return timezone.now >= self.deadline


class Category(models.Model):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="categories",
        related_query_name="category",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        related_name="categories",
        related_query_name="category",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "owner",
                Lower("name"),
                name="unique_category_name_per_user",
            ),
        ]


class Task(models.Model):

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        DOING = "doing", "Doing"
        DONE = "done", "Done"

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        related_query_name="task",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        related_name="tasks",
        related_query_name="task",
    )
    title = models.CharField(max_length=150)
    notes = models.TextField(null=True)
    due_date = models.DateTimeField(
        null=True,
    )
    priority = models.IntegerField(
        choices=Priority,
        null=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status,
        default=Status.NOT_STARTED,
    )
    prerequisites = models.ManyToManyField(
        to="self",
        symmetrical=False,
        null=True,
        related_name="dependents",
        related_query_name="dependent",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        related_name="tasks",
        related_query_name="task",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("title"),
                "owner",
                name="unique_task_title_per_user",
            ),
        ]
