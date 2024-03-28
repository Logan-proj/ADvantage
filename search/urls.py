from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_view, name='search'),
    path('search-ad/', views.search_ad, name='search_ad'),
    path('get-user-details/', views.get_user_details, name='get-user-details'),
    path('logon-hours/', views.get_logonHours, name='logon-hours'),
    path('user-details/<str:dn>/', views.user_details_view, name='user-details'),
]