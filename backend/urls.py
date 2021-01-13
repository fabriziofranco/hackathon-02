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
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from agricultores import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'departments', views.DepartmentViewSet, basename='departments')
router.register(r'regions', views.RegionViewSet, basename='regions')
router.register(r'districts', views.DistrictViewSet, basename='districts')

router.register(r'supplies', views.SupplyViewSet, basename='supplies')
router.register(r'advertisements', views.AdvertisementViewSet, basename='advertisements')
router.register(r'addressedTos', views.AddressedToViewSet, basename='addressedTos')
router.register(r'crops', views.PublishViewSet, basename='crops')
router.register(r'orders', views.OrderViewSet, basename='orders')


urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
