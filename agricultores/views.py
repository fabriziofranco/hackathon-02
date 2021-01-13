from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import permissions
from django.contrib.auth import get_user_model

from agricultores.models import Department, Region, District, Supply, Advertisement, AddressedTo, Publish, Order
from agricultores.serializers import UserSerializer, DepartmentSerializer, RegionSerializer, DistrictSerializer, \
    SuppliesSerializer, AdvertisementSerializer, AdressedToSerializer, PublishSerializer, OrderSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    user = get_user_model()
    queryset = user.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Department.objects.all().order_by('id')
    serializer_class = DepartmentSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]


class RegionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Region.objects.all().order_by('id')
    serializer_class = RegionSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]


class DistrictViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = District.objects.all().order_by('id')
    serializer_class = DistrictSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

class SupplyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Supply.objects.all().order_by('id')
    serializer_class = SuppliesSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

class AdvertisementViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Advertisement.objects.all().order_by('id')
    serializer_class = AdvertisementSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

class AddressedToViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = AddressedTo.objects.all().order_by('id')
    serializer_class = AdressedToSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

class PublishViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Publish.objects.all().order_by('id')
    serializer_class = PublishSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated]
