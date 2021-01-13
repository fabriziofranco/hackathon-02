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
    department = serializers.CharField(source='department.name')
    region = serializers.CharField(source='region.name')
    
    class Meta:
        model = District
        fields = ['id', 'name', 'department', 'region']


class RegionSerializer(serializers.ModelSerializer):
    department = serializers.CharField(source='department.name')
    
    class Meta:
        model = Region
        fields = ['id', 'name', 'department']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name']


class SuppliesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supply
        fields = '__all__'


class AdvertisementSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.phone_number')
    supply = serializers.CharField(source='supply.name')
    
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
