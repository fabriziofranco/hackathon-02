"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views

from agricultores import views
from agricultores import culqi

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'departments', views.DepartmentViewSet, basename='departments')
router.register(r'regions', views.RegionViewSet, basename='regions')
router.register(r'districts', views.DistrictViewSet, basename='districts')

router.register(r'supplys', views.SupplyViewSet, basename='supplys')
router.register(r'advertisements', views.AdvertisementViewSet, basename='advertisements')
router.register(r'addressedTos', views.AddressedToViewSet, basename='addressedTos')
router.register(r'publish', views.PublishViewSet, basename='publish')
router.register(r'order', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('phoneVerification/', views.PhoneVerification.as_view()),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('hello/', views.HelloView.as_view(), name='hello'),
    path('api/filter/', include('agricultores.api_urls')),
    path('uploadProfilePicture/', views.UploadProfilePicture.as_view()),
    re_path(r'uploadPubPicture/(?P<id>\d+)/', views.UploadPubPicture.as_view()),
    re_path(r'detetePubPicture/(?P<id>\d+)/', views.DeletePubPicture.as_view()),
    path('updateUbigeo/', views.ChangeUserUbigeo.as_view()),
    path('updateRol/', views.ChangeUserRol.as_view()),
    path('myInfo/', views.GetUserData.as_view()),
    path('myPub/', views.GetMyPub.as_view()),
    path('myAd/', views.GetMyAd.as_view()),
    path('myFeaturedPub/', views.GetMyFeaturedPub.as_view()),
    re_path(r'myPub/(?P<id>\d+)/', views.GetMyPubByID.as_view()),
    re_path(r'Pubs/(?P<id>\d+)/', views.GetPubs.as_view()),
    re_path(r'OrdersUser/(?P<id>\d+)/', views.GetOrders.as_view()),
    path('myOrder/', views.GetMyOrder.as_view()),
    path('myFeaturedOrder/', views.GetMyFeaturedOrder.as_view()),
    re_path(r'myOrder/(?P<id>\d+)/', views.GetMyOrderByID.as_view()),
    path('myProspects/', views.GetMyProspects.as_view()),
    path('mySuggestions/', views.GetMySuggestions.as_view()),
    path('purchaseCredits/', culqi.CreateChargeClient.as_view()),
    path('myCredits/', culqi.MyCredits.as_view()),
    path('postAd/', views.PostAd.as_view()),
    path('estimatePublic/', views.EstimatePublic.as_view()),
    path('getAdForIt/', views.GetAdForIt.as_view()),
    path('postUserFromWeb/', views.PostUserFromWeb.as_view()),
    path('deleteAd/', views.DeleteAd.as_view()),
    re_path(r'deleteAd/(?P<id>\d+)/', views.DeleteAd.as_view()),
    path('getSupplies/', views.GetSupplies.as_view()),
    re_path(r'getSupplies/(?P<id>\d+)/', views.GetSupplies.as_view()),
    path('addCredits/', views.AddCredits.as_view()),
    re_path(r'addCredits/(?P<id>\d+)/', views.AddCredits.as_view()),
    path('orderSupply/', views.OrderSupply.as_view()),
    re_path(r'orderSupply/(?P<id>\d+)/', views.OrderSupply.as_view()),
    path('publicationSupply/', views.PublicationSupply.as_view()),
    re_path(r'publicationSupply/(?P<id>\d+)/', views.PublicationSupply.as_view()),
    #  path('createOrder/', views.CreateMyOrder.as_view()),
    path('changePassword/', views.ChangePassword.as_view()),
]
