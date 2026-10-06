from django.urls import path
from . import views

app_name = 'rides'

urlpatterns = [
    path('', views.index, name='index'),
    path('rides/', views.ride_list, name='ride_list'),
]
