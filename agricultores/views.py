import os
from io import BytesIO

import twilio
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets
from rest_framework import permissions
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

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


class RegionFilterView(generics.ListAPIView):
    serializer_class = RegionSerializer
    pagination_class = None

    def get_queryset(self):
        department_id = self.request.query_params.get('department', '')
        # name_id = self.request.query_params.get('name', '')
        # return Region.objects.filter(department=department_id,name=name_id)
        return Region.objects.filter(department=department_id)


class DistrictFilterView(generics.ListAPIView):
    serializer_class = DistrictSerializer
    pagination_class = None

    def get_queryset(self):
        region_id = self.request.query_params.get('region', '')
        # name_id = self.request.query_params.get('name', '')
        # return Region.objects.filter(department=department_id,name=name_id)
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

    def get(self, request):
        data = serializers.serialize('json', self.get_queryset())
        return HttpResponse(data, content_type="application/json")

    def get_queryset(self):
        return get_user_model().objects.filter(id=self.request.user.id)
