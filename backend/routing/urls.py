from django.urls import path
from .views import health_check, plan_route

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('plan/', plan_route, name='plan_route'),
]
