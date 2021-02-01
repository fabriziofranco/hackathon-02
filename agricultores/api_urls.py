from django.urls import path, include
from agricultores.views import *

urlpatterns = [
    path('regions/', RegionFilterView.as_view()),
    path('districts/', DistrictFilterView.as_view()),
    path('pubs/', PublishFilterView.as_view()),
    path('compradores/', CompradorFilterView.as_view()),
    path('agricultores/', AgricultorFilterView.as_view()),
]
