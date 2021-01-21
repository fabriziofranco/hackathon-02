from django.urls import path, include
from agricultores.views import *

urlpatterns = [
    path('region/', TestView.as_view())
]
