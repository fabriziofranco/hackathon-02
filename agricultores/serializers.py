from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.contrib.auth import get_user_model

from agricultores.models import Department, District, Region, Supply, Advertisement, AddressedTo, Publish, Order


class UserSerializer(serializers.ModelSerializer):
    district = serializers.StringRelatedField()

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
            'district',
            'latitude',
            'longitude',
            'is_advertiser']


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']


class SuppliesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supply
        fields = '__all__'


class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement
        fields = '__all__'


class AdressedToSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressedTo
        fields = '__all__'


class PublishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publish
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'


# class DistrictSerializer(serializers.ModelSerializer):
#     users = UserSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = District
#         fields = ['id', 'name', 'users']
#
#
# class RegionSerializer(serializers.ModelSerializer):
#     districts = DistrictSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Region
#         fields = ['id', 'name', 'districts']
#
#
# class DepartmentSerializer(serializers.ModelSerializer):
#     regions = RegionSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Department
#         fields = ['id', 'name', 'regions']
