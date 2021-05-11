import json
import os
import datetime as dt
from io import BytesIO
import twilio
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets, status
from rest_framework import permissions
from django.contrib.auth import get_user_model
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
import environ
from twilio import base
from twilio.rest import Client
from agricultores.models import Department, Region, District, Supply, Advertisement, LinkedTo, Publish, Order, User
from agricultores.serializers import UserSerializer, DepartmentSerializer, RegionSerializer, DistrictSerializer, \
    SuppliesSerializer, AdvertisementSerializer, AdressedToSerializer, PublishSerializer, OrderSerializer
from rest_framework import generics
from backend.custom_storage import MediaStorage
from urllib.parse import urljoin, urlparse
from PIL import Image, ExifTags
from django.core.files.uploadedfile import InMemoryUploadedFile
from datetime import datetime
from datetime import date
import secrets
from django.db.models import Q
import random


class PublishFilterView(generics.ListAPIView):
    serializer_class = PublishSerializer
    pagination_class = None

    def get_queryset(self):
        supply_id = self.request.query_params.get('supply', 0)
        min_price = self.request.query_params.get('min_price', float('-inf'))
        max_price = self.request.query_params.get('max_price', float('inf'))
        min_date = self.request.query_params.get('min_date', dt.date.min)
        max_date = self.request.query_params.get('max_date', dt.date.max)
        department_id = self.request.query_params.get('department', 0)
        region_id = self.request.query_params.get('region', 0)

        temp = Publish.objects.filter(unit_price__gte=min_price,
                                      unit_price__lte=max_price,
                                      harvest_date__gte=min_date,
                                      harvest_date__lte=max_date,
                                      is_sold=False)
        if supply_id != 0:
            temp = temp.filter(supplies=supply_id)
        if department_id != 0:
            temp = temp.filter(user__district__department__id=department_id)
        if region_id != 0:
            temp = temp.filter(user__district__region__id=region_id)
        return temp


class OrderFilterView(generics.ListAPIView):
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        supply_id = self.request.query_params.get('supply', 0)
        min_price = self.request.query_params.get('min_price', float('-inf'))
        max_price = self.request.query_params.get('max_price', float('inf'))
        min_date = self.request.query_params.get('min_date', dt.date.min)
        max_date = self.request.query_params.get('max_date', dt.date.max)
        department_id = self.request.query_params.get('department', 0)
        region_id = self.request.query_params.get('region', 0)

        temp = Order.objects.filter(unit_price__gte=min_price,
                                    unit_price__lte=max_price,
                                    desired_harvest_date__gte=min_date,
                                    desired_harvest_date__lte=max_date,
                                    is_solved=False)
        if supply_id != 0:
            temp = temp.filter(supplies=supply_id)
        if department_id != 0:
            temp = temp.filter(user__district__department__id=department_id)
        if region_id != 0:
            temp = temp.filter(user__district__region__id=region_id)
        return temp


class CompradorFilterView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = None

    def get_queryset(self):
        supply_id = self.request.query_params.get('supply', 0)
        department_id = self.request.query_params.get('department', 0)
        region_id = self.request.query_params.get('region', 0)

        if supply_id == 0 and department_id == 0 and region_id == 0:
            return get_user_model().objects.filter(role="co")

        temp = User.objects.all()
        if supply_id != 0:
            users = Order.objects.filter(supplies=supply_id).values_list("user", flat=True).distinct()
            temp = temp.filter(id__in=users).exclude(id=self.request.user.id)
        if department_id != 0:
            temp = temp.filter(district__department__id=department_id)
        if region_id != 0:
            temp = temp.filter(district__region__id=region_id)
        return temp


class AgricultorFilterView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = None

    def get_queryset(self):
        supply_id = self.request.query_params.get('supply', 0)
        department_id = self.request.query_params.get('department', 0)
        region_id = self.request.query_params.get('region', 0)

        if supply_id == 0 and department_id == 0 and region_id == 0:
            return get_user_model().objects.filter(role="ag")

        temp = User.objects.all()
        if supply_id != 0:
            users = Publish.objects.filter(supplies=supply_id).values_list("user", flat=True).distinct()
            temp = temp.filter(id__in=users).exclude(id=self.request.user.id)
        if department_id != 0:
            temp = temp.filter(district__department__id=department_id)
        if region_id != 0:
            temp = temp.filter(district__region__id=region_id)
        return temp


class GetMyProspects(generics.ListAPIView):
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        my_supplies = Publish.objects.filter(user=self.request.user).values_list("supplies", flat=True).distinct()
        query_set = Order.objects.filter(supplies__in=my_supplies).exclude(user=self.request.user)
        return query_set


class GetMySuggestions(generics.ListAPIView):
    serializer_class = PublishSerializer
    pagination_class = None

    def get_queryset(self):
        my_supplies = Order.objects.filter(user=self.request.user).values_list("supplies", flat=True).distinct()
        query_set = Publish.objects.filter(supplies__in=my_supplies).exclude(user=self.request.user)
        return query_set


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


class SellPublicationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        try:
            supply_name = request.data.get('name')

            Supply.objects.filter(name=supply_name).update(sold_publications=F('sold_publications') + 1,
                                                           unsold_publications=F('unsold_publications') - 1)

            return HttpResponse('Updated correctly.', status=200)
        except Exception as e:
            return HttpResponse('Internal error.', status=400)


class SolveOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        try:
            supply_name = request.data.get('name')

            Supply.objects.filter(name=supply_name).update(solved_orders=F('solved_orders') + 1,
                                                           unsolved_orders=F('unsolved_orders') - 1)

            return HttpResponse('Updated correctly.', status=200)
        except Exception as e:
            return HttpResponse('Internal error.', status=400)


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
    action_permissions = {
        AllowAny: ['list', 'retrieve'],
        permissions.IsAdminUser: ['destroy', 'create', 'update', 'partial_update', 'list', 'retrieve'],
    }


class RegionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Region.objects.all().order_by('id')
    serializer_class = RegionSerializer
    pagination_class = None
    action_permissions = {
        AllowAny: ['list', 'retrieve'],
        permissions.IsAdminUser: ['destroy', 'create', 'update', 'partial_update', 'list', 'retrieve'],
    }


class DistrictViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = District.objects.all().order_by('id')
    serializer_class = DistrictSerializer
    pagination_class = None
    action_permissions = {
        AllowAny: ['list', 'retrieve'],
        permissions.IsAdminUser: ['destroy', 'create', 'update', 'partial_update', 'list', 'retrieve'],
    }


class SupplyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Supply.objects.all().order_by('id')
    serializer_class = SuppliesSerializer
    pagination_class = None
    action_permissions = {
        permissions.IsAuthenticated: ['list', 'retrieve'],
        permissions.IsAdminUser: ['destroy', 'create', 'update', 'partial_update', 'list', 'retrieve'],
    }


class AdvertisementViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Advertisement.objects.all().order_by('id')
    serializer_class = AdvertisementSerializer
    pagination_class = None
    permission_classes = [permissions.IsAdminUser]


class AddressedToViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = LinkedTo.objects.all().order_by('id')
    serializer_class = AdressedToSerializer
    pagination_class = None
    permission_classes = [permissions.IsAdminUser]


class PublishViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Publish.objects.all().order_by('id')
    serializer_class = PublishSerializer
    pagination_class = None
    permission_classes = [ActionBasedPermission, ]
    action_permissions = {
        permissions.IsAuthenticated: ['list', 'retrieve'],
        permissions.IsAdminUser: ['destroy', 'create', 'update', 'partial_update', 'list', 'retrieve'],
    }


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Order.objects.all().order_by('id')
    serializer_class = OrderSerializer
    pagination_class = None
    permission_classes = [ActionBasedPermission, ]
    action_permissions = {
        permissions.IsAuthenticated: ['list', 'retrieve'],
        permissions.IsAdminUser: ['destroy', 'create', 'update', 'partial_update', 'list', 'retrieve'],
    }


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


class ChangePassword(APIView):
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

    def parse_phone_number(self, phone_number):
        return "+" + phone_number

    def get(self, request):
        phone_number = self.parse_phone_number(self.request.query_params.get("phone_number"))
        try:
            response = self.send_verification_token(phone_number, 'sms')
            return Response(response.status)
        except twilio.base.exceptions.TwilioRestException as e:
            return HttpResponse(e, status=400)

    def post(self, request):
        code = request.data.get("code")
        phone_number = self.parse_phone_number(self.request.data.get("phone_number"))
        new_password = request.data.get("new_password")
        try:
            response = self.check_verification_token(phone_number, code)
            if response.status == "approved":
                user = User.objects.get(phone_number=phone_number)
                user.set_password(new_password)
                user.save()
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


class UploadPubPicture(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, **kwargs):
        # APPEND IMAGE
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

        thumb_io = BytesIO()
        img.save(thumb_io, format='JPEG', quality=50, optimize=True)
        image_file = InMemoryUploadedFile(thumb_io, None, str(file_obj.name) + '.jpg', 'image/jpeg', thumb_io.tell,
                                          None)

        # organize a path for the file in bucket
        file_directory_within_bucket = 'pub_pictures/'

        # synthesize a full file path; note that we included the filename
        file_path_within_bucket = os.path.join(
            file_directory_within_bucket,
            secrets.token_urlsafe(22)
        )

        media_storage = MediaStorage()

        media_storage.save(file_path_within_bucket, image_file)
        file_url = media_storage.url(file_path_within_bucket)
        no_params_url = urljoin(file_url, urlparse(file_url).path)

        id_cultivo = self.kwargs['id']

        pub = Publish.objects.get(id=id_cultivo, user_id=request.user.id)
        pub.picture_URLs.append(no_params_url)
        pub.save()

        return JsonResponse({
            'message': 'OK',
            'fileUrl': no_params_url,
        })


class DeletePubPicture(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, **kwargs):
        try:

            id_cultivo = self.kwargs['id']
            list_of_urls_to_delete = request.data['picture_URLs']

            # organize a path for the file in bucket
            file_directory_within_bucket = 'pub_pictures/'

            media_storage = MediaStorage()

            pub = Publish.objects.get(id=id_cultivo, user_id=request.user.id)

            for url in list_of_urls_to_delete:
                file_path_within_bucket = os.path.join(
                    file_directory_within_bucket,
                    url.rsplit('/', 1)[-1]
                )
                print(file_path_within_bucket)
                media_storage.delete(file_path_within_bucket)
                pub.picture_URLs.remove(url)

            pub.save()

            return HttpResponse('Elementos eliminados correctamente.', status=204)

        except Exception as e:
            return HttpResponse('Internal error.', status=400)


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


class GetUserData(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user.phone_number
        return get_user_model().objects.filter(phone_number=user)


class GetMyOrderByID(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['id']
        return Order.objects.filter(user=user, id=pk)

    def put(self, request, *args, **kwargs):
        device = self.get_queryset().first()
        serializer = OrderSerializer(device, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        self.get_queryset().first().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetMyOrder(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user).order_by('is_solved')

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        return super(GetMyOrder, self).perform_create(serializer)


class GetPubs(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublishSerializer
    pagination_class = None

    def get_queryset(self):
        pk = self.kwargs['id']
        return Publish.objects.filter(user=pk)


class GetOrders(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        pk = self.kwargs['id']
        return Order.objects.filter(user=pk)


class GetMyPubByID(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublishSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['id']
        return Publish.objects.filter(user=user, id=pk)

    def put(self, request, *args, **kwargs):
        device = self.get_queryset().first()
        serializer = PublishSerializer(device, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        self.get_queryset().first().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetMyPub(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublishSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return Publish.objects.filter(user=user).order_by('is_sold')

    def perform_create(self, serializer):
        serializer.validated_data['user'] = self.request.user
        return super(GetMyPub, self).perform_create(serializer)


class PostAd(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdvertisementSerializer

    def post(self, request):
        try:
            user = self.request.user

            remaining_credits = request.data.get('remaining_credits')
            if int(remaining_credits) > user.number_of_credits:
                return HttpResponse(json.dumps({"message": "No hay suficientes creditos en su cuenta"}), status=400,
                                    content_type="application/json")

            get_user_model().objects.filter(id=self.request.user.id).update(number_of_credits=
                                                                            F('number_of_credits') - int(
                                                                                remaining_credits))

            if request.data.get('region_id') != 0:
                region = Region.objects.filter(pk=request.data.get('region_id')).first()
            else:
                region = None

            if request.data.get('department_id') != 0:
                department = Department.objects.filter(pk=request.data.get('department_id')).first()
            else:
                department = None

            if request.data.get('district_id') != 0:
                district = District.objects.filter(pk=request.data.get('district_id')).first()
            else:
                district = None

            for_orders = request.data.get('for_orders')
            for_publications = request.data.get('for_publications')
            picture_URL = request.data.get('picture_URL')
            URL = request.data.get('URL')
            name = request.data.get('name')

            beginning_sowing_date = datetime.strptime(request.data.get('beginning_sowing_date'), '%d/%m/%y '
                                                                                                 '%H:%M:%S')
            print(beginning_sowing_date)

            if beginning_sowing_date.year == 2020:
                beginning_sowing_date = None

            ending_sowing_date = datetime.strptime(request.data.get('ending_sowing_date'), '%d/%m/%y %H:%M:%S')

            if ending_sowing_date.year == 2020:
                ending_sowing_date = None

            beginning_harvest_date = datetime.strptime(request.data.get('beginning_harvest_date'), '%d/%m/%y %H:%M:%S')

            if beginning_harvest_date.year == 2020:
                beginning_harvest_date = None

            ending_harvest_date = datetime.strptime(request.data.get('ending_harvest_date'), '%d/%m/%y %H:%M:%S')

            if ending_harvest_date.year == 2020:
                ending_harvest_date = None
            ad_ojb = Advertisement.objects.create(user=user,
                                                  remaining_credits=remaining_credits,
                                                  original_credits=remaining_credits,
                                                  region=region,
                                                  department=department,
                                                  district=district,
                                                  for_orders=for_orders,
                                                  for_publications=for_publications,
                                                  URL=URL,
                                                  name=name,
                                                  beginning_sowing_date=beginning_sowing_date,
                                                  ending_sowing_date=ending_sowing_date,
                                                  beginning_harvest_date=beginning_harvest_date,
                                                  ending_harvest_date=ending_harvest_date)
            for supply_obj in request.data.getlist("supplies"):
                LinkedTo.objects.create(supply=Supply.objects.filter(pk=supply_obj).first(), advertisement=ad_ojb)

            file_obj = request.FILES.get('file', '')
            img = Image.open(file_obj)
            img.thumbnail((500, 500), Image.ANTIALIAS)
            thumb_io = BytesIO()
            img.save(thumb_io, format='JPEG')
            image_file = InMemoryUploadedFile(thumb_io, None, str(file_obj.name) + '.jpg', 'image/jpeg', thumb_io.tell,
                                              None)

            # organize a path for the file in bucket
            file_directory_within_bucket = 'ad_pictures/'

            # synthesize a full file path; note that we included the filename
            file_path_within_bucket = os.path.join(
                file_directory_within_bucket,
                str(ad_ojb.id)
            )

            media_storage = MediaStorage()

            media_storage.save(file_path_within_bucket, image_file)
            file_url = media_storage.url(file_path_within_bucket)
            no_params_url = urljoin(file_url, urlparse(file_url).path)
            ad_ojb.picture_URL = no_params_url
            ad_ojb.save()

            return HttpResponse('Created correctly.', status=200)
        except Exception as e:
            return HttpResponse(json.dumps({"message": e}), status=400, content_type="application/json")


class EstimatePublic(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total = 0

        supplies_arr = self.request.query_params.getlist('supplies', [])
        department_id = self.request.query_params.get('department_id', 0)
        region_id = self.request.query_params.get('region_id', 0)
        district_id = self.request.query_params.get('district_id', 0)
        for_orders = self.request.query_params.get('for_orders', True)
        for_publications = self.request.query_params.get('for_publications', True)

        beginning_sowing_date = self.request.query_params.get('beginning_sowing_date', dt.date.min)
        ending_sowing_date = self.request.query_params.get('ending_sowing_date', dt.date.max)
        beginning_harvest_date = self.request.query_params.get('beginning_harvest_date', dt.date.min)
        ending_harvest_date = self.request.query_params.get('ending_harvest_date', dt.date.max)

        if for_orders:
            temp = Order.objects.filter(desired_harvest_date__gte=beginning_harvest_date,
                                        desired_harvest_date__lte=ending_harvest_date,
                                        desired_sowing_date__gte=beginning_sowing_date,
                                        desired_sowing_date__lte=ending_sowing_date,
                                        is_solved=False)

            if supplies_arr:
                temp = temp.filter(supplies__in=supplies_arr)
            if department_id != 0:
                temp = temp.filter(user__district__department__id=department_id)
            if region_id != 0:
                temp = temp.filter(user__district__region__id=region_id)
            if district_id != 0:
                temp = temp.filter(user__district__id=district_id)

            total += len(temp)

        if for_publications:
            temp_2 = Publish.objects.filter(harvest_date__gte=beginning_harvest_date,
                                            harvest_date__lte=ending_harvest_date,
                                            sowing_date__gte=beginning_sowing_date,
                                            sowing_date__lte=ending_sowing_date,
                                            is_sold=False)

            if supplies_arr:
                temp_2 = temp_2.filter(supplies__in=supplies_arr)
            if department_id != 0:
                temp_2 = temp_2.filter(user__district__department__id=department_id)
            if region_id != 0:
                temp_2 = temp_2.filter(user__district__region__id=region_id)
            if district_id != 0:
                temp_2 = temp_2.filter(user__district__id=district_id)

            total += len(temp_2)

        return JsonResponse({
            'total': total,
        })


class GetMyFeaturedPub(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PublishSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return Publish.objects.filter(user=user).order_by("-pk")[:4]


class GetMyFeaturedOrder(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user).order_by("-pk")[:4]


class GetMyAd(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdvertisementSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return Advertisement.objects.filter(user=user)


# class updatePublish(generics.ListCreateAPIView):
#

class GetAdForIt(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get(self, request):
        obj_id = self.request.query_params.get('id', 0)
        obj_type = self.request.query_params.get('type', 'pub')  # type can be 'pub' and 'order'

        if obj_type == 'pub':
            pub_obj = Publish.objects.filter(id=obj_id).first()
            linkedToObjects = LinkedTo.objects.filter(supply__id=pub_obj.supplies.id)
            print(linkedToObjects)
            adIds = []
            adObjects = []
            for object in linkedToObjects:
                adIds.append(object.advertisement.id)
            if adIds:
                adObjects = Advertisement.objects.filter(id__in=adIds, remaining_credits__gt=0, for_publications=True)
                adObjects = adObjects.filter(Q(department=None) | Q(department__id=pub_obj.user.district.department.id))
                adObjects = adObjects.filter(Q(region=None) | Q(region__id=pub_obj.user.district.region.id))
                adObjects = adObjects.filter(Q(district=None) | Q(district__id=pub_obj.user.district.id))
                adObjects = adObjects.filter(
                    Q(beginning_sowing_date=None) | Q(beginning_sowing_date__gte=pub_obj.sowing_date))
                adObjects = adObjects.filter(
                    Q(ending_sowing_date=None) | Q(ending_sowing_date__lte=pub_obj.sowing_date))
                adObjects = adObjects.filter(
                    Q(beginning_harvest_date=None) | Q(beginning_harvest_date__gte=pub_obj.harvest_date))
                adObjects = adObjects.filter(
                    Q(ending_harvest_date=None) | Q(ending_harvest_date__lte=pub_obj.harvest_date))

        elif obj_type == 'order':
            order_obj = Order.objects.filter(id=obj_id).first()
            linkedToObjects = LinkedTo.objects.filter(supply__id=order_obj.supplies.id)
            adIds = []
            adObjects = []
            for object in linkedToObjects:
                adIds.append(object.advertisement.id)
            if adIds:
                adObjects = Advertisement.objects.filter(id__in=adIds, remaining_credits__gt=0, for_publications=True)
                adObjects = adObjects.filter(
                    Q(department=None) | Q(department__id=order_obj.user.district.department.id))
                adObjects = adObjects.filter(Q(region=None) | Q(region__id=order_obj.user.district.region.id))
                adObjects = adObjects.filter(Q(district=None) | Q(district__id=order_obj.user.district.id))
                adObjects = adObjects.filter(
                    Q(beginning_sowing_date=None) | Q(beginning_sowing_date__gte=order_obj.desired_sowing_date))
                adObjects = adObjects.filter(
                    Q(ending_sowing_date=None) | Q(ending_sowing_date__lte=order_obj.desired_sowing_date))
                adObjects = adObjects.filter(
                    Q(beginning_harvest_date=None) | Q(beginning_harvest_date__gte=order_obj.desired_harvest_date))
                adObjects = adObjects.filter(
                    Q(ending_harvest_date=None) | Q(ending_harvest_date__lte=order_obj.desired_harvest_date))
        if adObjects:
            it = random.choice(adObjects)
            id_it = it.id
            Advertisement.objects.filter(id=id_it).update(remaining_credits=F('remaining_credits') - 1)
            return JsonResponse({
                'data': True,
                'URL': it.URL,
                'picture_URL': it.picture_URL,
            })
        else:
            return JsonResponse({
                'data': False,
            })


class PostUserFromWeb(generics.ListCreateAPIView):
    # permission_classes = [permissions.IsAuthenticated]

    # serializer_class = AdvertisementSerializer
    def post(self, request, **kwargs):
        try:
            first_name = request.data.get('first_name')
            last_name = request.data.get('last_name')
            phone_number = request.data.get('phone_number')
            if get_user_model().objects.filter(phone_number=phone_number):
                return HttpResponse(json.dumps({"message": "Teléfono ya registrado"}), status=400,
                                    content_type="application/json")
            password = request.data.get('password')
            DNI = request.data.get('DNI')
            RUC = request.data.get('RUC')
            district_id = request.data.get('district_id')
            email = request.data.get('email')
            district_obj = District.objects.filter(id=district_id).first()
            user = get_user_model().objects.create(first_name=first_name,
                                                   last_name=last_name,
                                                   phone_number=phone_number,
                                                   DNI=DNI,
                                                   email=email,
                                                   role='an',
                                                   RUC=RUC,
                                                   district=district_obj)

            file_obj = request.FILES.get('file', '')
            if file_obj:
                img = Image.open(file_obj)
                get_exif_info = img._getexif()
                if get_exif_info:
                    exif = dict((ExifTags.TAGS[k], v) for k, v in get_exif_info.items() if k in ExifTags.TAGS)
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
                    user.phone_number.as_e164[1:]
                )

                media_storage = MediaStorage()

                media_storage.save(file_path_within_bucket, image_file)
                file_url = media_storage.url(file_path_within_bucket)
                no_params_url = urljoin(file_url, urlparse(file_url).path)
                user.profile_picture_URL = no_params_url
            user.set_password(password)
            user.save()

            return HttpResponse('Created correctly.', status=200)
        except Exception as e:
            return HttpResponse(json.dumps({"message": e}), status=400, content_type="application/json")


class DeleteAd(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, **kwargs):
        try:
            ad_id = self.kwargs['id']
            credits_ret = Advertisement.objects.filter(id=ad_id).first().remaining_credits
            Advertisement.objects.filter(id=ad_id).first().delete()

            get_user_model().objects.filter(id=self.request.user.id).update(number_of_credits=
                                                                            F('number_of_credits') + int(credits_ret))

            return HttpResponse('Removed correctly.', status=200)
        except Exception as e:
            return HttpResponse(json.dumps({"message": e}), status=400, content_type="application/json")


class GetSupplies(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, **kwargs):
        try:
            ad_id = self.kwargs['id']
            ad_obj = Advertisement.objects.filter(id=ad_id).first()
            linkedToObjects = LinkedTo.objects.filter(advertisement=ad_obj)
            supplyNames = []
            for obj in linkedToObjects:
                it = obj.supply.name
                if it not in supplyNames:
                    supplyNames.append(it)
            if len(supplyNames) == len(Supply.objects.all()):
                supplyNames = ["Todos los insumos"]
            return HttpResponse(json.dumps({"supplies": supplyNames}), status=200)
        except Exception as e:
            return HttpResponse(json.dumps({"message": e}), status=400, content_type="application/json")


class AddCredits(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, **kwargs):
        try:
            ad_id = self.kwargs['id']
            user = self.request.user
            new_credits = request.data.get('credits')
            if int(new_credits) > user.number_of_credits:
                return HttpResponse(json.dumps({"message": "No hay suficientes creditos en su cuenta"}), status=400,
                                    content_type="application/json")

            Advertisement.objects.filter(id=ad_id).update(remaining_credits=F('remaining_credits') + new_credits,
                                                          original_credits=F('original_credits') + new_credits)

            get_user_model().objects.filter(id=self.request.user.id).update(number_of_credits=
                                                                            F('number_of_credits') - int(new_credits))

            return HttpResponse('Updated correctly.', status=200)
        except Exception as e:
            return HttpResponse(json.dumps({"message": e}), status=400, content_type="application/json")
