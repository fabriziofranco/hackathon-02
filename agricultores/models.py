from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.

class Department(models.Model):
    name = models.CharField(max_length=35)

    def __str__(self):
        return self.name


class Region(models.Model):
    department = models.ForeignKey(Department, related_name='regions', on_delete=models.CASCADE)
    name = models.CharField(max_length=35)

    def __str__(self):
        return self.name


class District(models.Model):
    region = models.ForeignKey(Region, related_name='districts', on_delete=models.CASCADE)
    department = models.ForeignKey(Department, related_name='districts', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        if not phone_number:
            raise ValueError('Users must have a phone number')

        user = self.model(
            phone_number=phone_number
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None):
        user = self.create_user(
            phone_number,
            password=password
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    ROL = [('ag', 'Agricultor'), ('an', 'Anunciante'), ('co', 'Comprador')]
    phone_number = PhoneNumberField(null=False, blank=False, unique=True)
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        blank=True,
        null=True,
    )
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    profile_picture_URL = models.URLField(null=True, blank=True)
    number_of_credits = models.IntegerField(default=0)
    RUC = models.CharField(max_length=11, null=True, blank=True)
    DNI = models.CharField(max_length=8, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    district = models.ForeignKey(District, related_name='users', on_delete=models.CASCADE, null=True, blank=True)
    is_advertiser = models.BooleanField(default=False)
    role = models.CharField(max_length=2, choices=ROL, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return str(self.phone_number)

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin


class Supply(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Advertisement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE)
    reach = models.IntegerField()
    harvest_date = models.DateTimeField()
    sowing_date = models.DateTimeField()


class AddressedTo(models.Model):
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)


WEIGHT_UNITS = [
    ('kg', 'Kilogramos'),
    ('ton', 'Toneladas'),
]

AREA_UNITS = [
    ('hm2', 'Hectáreas'),
    ('m2', 'Metros cuadrados')
]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    supplies = models.ForeignKey(Supply, on_delete=models.CASCADE)
    weight_unit = models.CharField(max_length=3, choices=WEIGHT_UNITS)
    unit_price = models.FloatField()
    area_unit = models.CharField(max_length=3, choices=AREA_UNITS)
    area = models.FloatField()
    desired_harvest_date = models.DateTimeField()
    desired_sowing_date = models.DateTimeField()


class Publish(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    supplies = models.ForeignKey(Supply, on_delete=models.CASCADE)
    weight_unit = models.CharField(max_length=3, choices=WEIGHT_UNITS)
    unit_price = models.FloatField()
    area_unit = models.CharField(max_length=3, choices=AREA_UNITS)
    area = models.FloatField()
    harvest_date = models.DateTimeField()
    sowing_date = models.DateTimeField()
    picture_URLs = ArrayField(models.URLField(null=True, blank=True), blank=True)
