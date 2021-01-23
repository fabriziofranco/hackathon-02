from django.contrib.auth.models import User, Group
from rest_framework import serializers
from django.contrib.auth import get_user_model

from agricultores.models import Department, District, Region, Supply, Advertisement, AddressedTo, Publish, Order


class UserSerializer(serializers.ModelSerializer):
    district = serializers.StringRelatedField()
    password = serializers.CharField(write_only=True)

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
            'is_advertiser',
            'role',
            'is_verified',
            'password'
        ]

    def create(self, validated_data):
        user = get_user_model().objects.create(
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            DNI=validated_data['DNI'],
            RUC=validated_data['RUC'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


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
    supplies = SuppliesSerializer()

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
