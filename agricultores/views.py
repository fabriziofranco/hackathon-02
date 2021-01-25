import os
import datetime
from io import BytesIO
import twilio
from django.core import serializers
from django.http import HttpResponse, JsonResponse, Http404
from rest_framework import viewsets
from rest_framework import permissions
from django.contrib.auth import get_user_model
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from purl import URL
import environ
from twilio import base
from twilio.rest import Client

from agricultores.models import Department, Region, District, Supply, Advertisement, AddressedTo, Publish, Order
from agricultores.serializers import UserSerializer, DepartmentSerializer, RegionSerializer, DistrictSerializer, \
    SuppliesSerializer, AdvertisementSerializer, AdressedToSerializer, PublishSerializer, OrderSerializer

from rest_framework import generics

from backend.custom_storage import MediaStorage

from urllib.parse import urljoin, urlparse

from PIL import Image, ImageOps, ExifTags
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.base import ContentFile, File


class PublishFilterView(generics.ListAPIView):
    serializer_class = PublishSerializer
    pagination_class = None

    def get_queryset(self):
        supply_id = self.request.query_params.get('supply', 0)
        min_price = self.request.query_params.get('min_price', float('-inf'))
        max_price = self.request.query_params.get('max_price', float('inf'))
        min_date = self.request.query_params.get('min_date', datetime.date.min)
        max_date = self.request.query_params.get('max_date', datetime.date.max)
        department_id = self.request.query_params.get('department', 0)
        region_id = self.request.query_params.get('region', 0)

        temp = Publish.objects.filter(unit_price__gte=min_price,
                                      unit_price__lte=max_price,
                                      harvest_date__gte=min_date,
                                      harvest_date__lte=max_date)
        if supply_id != 0:
            temp = temp.filter(supplies=supply_id)
        if department_id != 0:
            temp = temp.filter(user__district__department__id=department_id)
        if region_id != 0:
            temp = temp.filter(user__district__region__id=region_id)
        return temp


class RegionFilterView(generics.ListAPIView):
    serializer_class = RegionSerializer
    pagination_class = None

    def get_queryset(self):
        department_id = self.request.query_params.get('department', '')
        return Region.objects.filter(department=department_id)


class DistrictFilterView(generics.ListAPIView):
    serializer_class = DistrictSerializer
    pagination_class = None

    def get_queryset(self):
        region_id = self.request.query_params.get('region', '')
        return District.objects.filter(region=region_id)


class ActionBasedPermission(AllowAny):
    """
    Grant or deny access to a view, based on a mapping in view.action_permissions
    """

    def has_permission(self, request, view):
        for klass, actions in getattr(view, 'action_permissions', {}).items():
            if view.action in actions:
                return klass().has_permission(request, view)
        return False


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    user = get_user_model()
    queryset = user.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [ActionBasedPermission, ]
    action_permissions = {
        permissions.IsAuthenticated: ['update', 'partial_update', 'list', 'retrieve'],
        permissions.IsAdminUser: ['destroy'],
        AllowAny: ['create']
    }


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


class PhoneVerification(APIView):
    permission_classes = [permissions.IsAuthenticated]
    client = Client(environ.Env().str('TWILIO_ACCOUNT_SID'), environ.Env().str('TWILIO_AUTH_TOKEN'))

    def send_verification_token(self, phone_number, channel):
        verification = self.client.verify \
            .services(environ.Env().str('TWILIO_SERVICE')) \
            .verifications \
            .create(to=phone_number, channel=channel)
        return verification

    def check_verification_token(self, phone_number, code):
        verification_check = self.client.verify \
            .services(environ.Env().str('TWILIO_SERVICE')) \
            .verification_checks \
            .create(to=phone_number, code=code)
        return verification_check

    def get(self, request):
        try:
            response = self.send_verification_token(request.user.phone_number.as_e164, 'sms')
            return Response(response.status)
        except twilio.base.exceptions.TwilioRestException as e:
            return HttpResponse(e, status=400)

    def post(self, request):
        code = request.data.get('code')
        try:
            response = self.check_verification_token(request.user.phone_number.as_e164, code)
            if response.status == 'approved':
                request.user.is_verified = True
                request.user.save()
            return Response(response.status)
        except twilio.base.exceptions.TwilioRestException as e:
            return HttpResponse(e, status=400)


class HelloView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        content = {'message': 'Hello, World!'}
        return Response(content)


class UploadProfilePicture(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, **kwargs):
        file_obj = request.FILES.get('file', '')

        # Compressing Image and Preventing Rotation
        img = Image.open(file_obj)
        exif = dict((ExifTags.TAGS[k], v) for k, v in img._getexif().items() if k in ExifTags.TAGS)
        if exif['Orientation'] == 3:
            img = img.rotate(180, expand=True)
        elif exif['Orientation'] == 6:
            img = img.rotate(270, expand=True)
        elif exif['Orientation'] == 8:
            img = img.rotate(90, expand=True)

        img.thumbnail((500, 500), Image.ANTIALIAS)
        thumb_io = BytesIO()
        img.save(thumb_io, format='JPEG')
        image_file = InMemoryUploadedFile(thumb_io, None, str(file_obj.name) + '.jpg', 'image/jpeg', thumb_io.tell,
                                          None)

        # organize a path for the file in bucket
        file_directory_within_bucket = 'profile_pictures/'

        # synthesize a full file path; note that we included the filename
        file_path_within_bucket = os.path.join(
            file_directory_within_bucket,
            request.user.phone_number.as_e164[1:]
        )

        media_storage = MediaStorage()

        media_storage.save(file_path_within_bucket, image_file)
        file_url = media_storage.url(file_path_within_bucket)
        no_params_url = urljoin(file_url, urlparse(file_url).path)
        request.user.profile_picture_URL = no_params_url
        request.user.save()

        return JsonResponse({
            'message': 'OK',
            'fileUrl': no_params_url,
        })


class ChangeUserUbigeo(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        try:
            district = request.data.get('district')
            lat = request.data.get('lat')
            lon = request.data.get('lon')
            request.user.district = District.objects.get(id=district)
            request.user.latitude = float(lat)
            request.user.longitude = float(lon)
            request.user.save()
            return HttpResponse('User updated correctly.', status=200)
        except Exception as e:
            return HttpResponse('Internal error.', status=400)


class ChangeUserRol(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        try:
            role = request.data.get('role')
            if role != 'ag' and role != 'an' and role != 'co':
                return HttpResponse('Rol seleccionado no existe.', status=404)
            request.user.role = role
            request.user.save()
            return HttpResponse('Rol updated correctly.', status=200)
        except Exception as e:
            return HttpResponse('Internal error.', status=400)


class GetUserData(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublishSerializer

    def get(self, request):
        data = serializers.serialize('json', self.get_queryset(), use_natural_foreign_keys=True)
        return HttpResponse(data, content_type="application/json")

    def get_queryset(self):
        return get_user_model().objects.filter(id=self.request.user.id)


class GetMyPub(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublishSerializer
    pagination_class = None

    def get_object(self, request, pk):
        try:
            return Publish.objects.get(pk=pk, user=self.request.user.id)
        except Publish.DoesNotExist:
            raise Http404

    def put(self, request, pk):
        publish = self.get_object(request, pk=pk)
        try:
            for field in request.data.keys():
                if field == 'supplies':
                    supplies = request.data.get('supplies')
                    publish.supplies = Supply.objects.get(id=int(supplies))
                elif field == 'picture_URL':
                    publish.harvest_date = URL(request.data.get('picture_URL'))
                elif field == 'unit':
                    publish.unit = str(request.data.get('unit'))
                elif field == 'quantity':
                    publish.quantity = int(request.data.get('quantity'))
                elif field == 'harvest_date':
                    publish.harvest_date = request.data.get('harvest_date')
                elif field == 'sowing_date':
                    publish.sowing_date = request.data.get('sowing_date')
                elif field == 'unit_price':
                    publish.unit_price = float(request.data.get('unit_price'))
            publish.save()
            return self.get(request, pk=pk)
        except Exception as e:
            return HttpResponse('Internal error.', status=400)

    def get_queryset(self, pk=0):
        queryset = Publish.objects.filter(user=self.request.user.id)
        if pk != 0:
            queryset = queryset.filter(id=pk)
        return queryset

    def get(self, request, pk=0):
        data = serializers.serialize('json', self.get_queryset(pk=pk), use_natural_foreign_keys=False)
        if data == '[]':
            return HttpResponse('Not Found.', status=404)
        return HttpResponse(data, content_type="application/json")


class GetMyOrder(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = None

    def get_object(self, pk):
        try:
            # return Order.objects.get(pk=pk, user=2)
            return Order.objects.get(pk=pk, user=self.request.user.id)
        except Order.DoesNotExist:
            raise Http404

    def put(self, request):
        id_order = self.request.query_params.get('id', 0)
        order = self.get_object(id_order)
        try:
            for field in request.data.keys():
                if field == 'supplies':
                    supplies = request.data.get('supplies')
                    order.supplies = Supply.objects.get(id=int(supplies))
                elif field == 'unit':
                    order.unit = str(request.data.get('unit'))
                elif field == 'number':
                    order.number = int(request.data.get('number'))
                elif field == 'desire_harvest_date':
                    order.desire_harvest_date = request.data.get('desire_harvest_date')
                elif field == 'desire_sowing_date':
                    order.desire_sowing_date = request.data.get('desire_sowing_date')
                elif field == 'unit_price':
                    order.unit_price = float(request.data.get('unit_price'))

            order.save()
            return HttpResponse('Updated correctly.', status=200)
        except Exception as e:
            return HttpResponse('Internal error.', status=400)

    def get_queryset(self):
        id_order = self.request.query_params.get('id', 0)
        # queryset = Order.objects.filter(user=2)
        queryset = Order.objects.filter(user=self.request.user.id)
        if id_order != 0:
            queryset = queryset.filter(id=id_order)
        return queryset

    def get(self, request):
        data = serializers.serialize('json', self.get_queryset(), use_natural_foreign_keys=False)
        return HttpResponse(data, content_type="application/json")

