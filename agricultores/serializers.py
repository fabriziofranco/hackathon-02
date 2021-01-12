from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.contrib.auth import get_user_model

from agricultores.models import Department, District, Region


class UserSerializer(serializers.HyperlinkedModelSerializer):# TRACK

    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'phone_number',
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


class DistrictSerializer(serializers.HyperlinkedModelSerializer): # ALBUM
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = District
        fields = ['id', 'name','users']


class RegionSerializer(serializers.HyperlinkedModelSerializer):
    districts = DistrictSerializer(many=True, read_only=True)

    class Meta:
        model = Region
        fields = ['id', 'name', 'districts']


class DepartmentSerializer(serializers.HyperlinkedModelSerializer):
    regions = RegionSerializer(many=True, read_only=True)

    class Meta:
        model = Department
        fields = ['id', 'name', 'regions']
