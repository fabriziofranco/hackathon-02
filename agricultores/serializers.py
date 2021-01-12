from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.contrib.auth import get_user_model

from agricultores.models import Department, District, Region


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['phone_number',
                  'email',
                  'first_name',
                  'last_name',
                  'profile_picture_URL',
                  'number_of_credits',
                  'RUC',
                  'DNI',
                  'latitude',
                  'longitude',
                  'is_advertiser']


class DepartmentSerializer(serializers.HyperlinkedModelSerializer):
    #district = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ['name']


class RegionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Region
        fields = ['name','department']


class DistrictSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = District
        fields = ['name','region','department']
