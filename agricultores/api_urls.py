from django.urls import path, include
from agricultores.views import *

urlpatterns = [
    path('regions/', RegionFilterView.as_view()),
    path('districts/', DistrictFilterView.as_view()),
]
