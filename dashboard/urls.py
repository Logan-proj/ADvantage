from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('settings/', views.settings_view, name='dashboard-settings'),
    path('search-ad/', views.search_ad, name='search_ad'),
    path('user-details/', views.user_details, name='user-details'),
]