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
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views

from agricultores import views

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
    url(r'phoneVerification/', views.PhoneVerification.as_view()),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('hello/', views.HelloView.as_view(), name='hello'),
]
