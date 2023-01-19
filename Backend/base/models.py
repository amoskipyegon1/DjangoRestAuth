from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.timezone import now


class UserManager(BaseUserManager):
    def create_user(self, emailAddress, firstName, password=None):
        if not emailAddress:
            raise ValueError("You must enter Email Address")

        if not firstName:
            raise ValueError("You must enter firstName")

        user = self.model(emailAddress=emailAddress, firstName=firstName)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, emailAddress, firstName, password=None):
        user = self.create_user(emailAddress, firstName, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class BaseUser(AbstractBaseUser):
    emailAddress = models.EmailField(
        verbose_name="email address", max_length=255, unique=True
    )
    firstName = models.CharField(max_length=255)
    lastName = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "emailAddress"
    REQUIRED_FIELDS = ["firstName"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "User"

    def __str__(self) -> str:
        return self.emailAddress

    @staticmethod
    def has_perm(perm, obj=None):
        return True

    @staticmethod
    def has_module_perms(app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin
