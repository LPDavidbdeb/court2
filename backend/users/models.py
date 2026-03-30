from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Add custom fields here if needed
    # For example:
    # company_name = models.CharField(max_length=100, blank=True, null=True)

    # Add related_name to avoid clashes with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions '\
                    'granted to each of their groups.',
        related_name="customuser_set", # Custom related name
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set", # Custom related name
        related_query_name="customuser",
    )

    def __str__(self):
        return self.email
