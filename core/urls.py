from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    RegisterViewSet, LoginViewSet, LogoutViewSet, PasswordResetViewSet,
    CarViewSet, ChatMessageViewSet, CommentViewSet, CarFilterView , FavoriteCarViewSet
)

# Əsas router
router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'login', LoginViewSet, basename='login')
router.register(r'logout', LogoutViewSet, basename='logout')
router.register(r'password-reset', PasswordResetViewSet, basename='password-reset')
router.register(r'cars', CarViewSet, basename='car')
router.register(r'chat', ChatMessageViewSet, basename='chat')
router.register(r'favorites', FavoriteCarViewSet, basename='favorites')

# Nested router: cars/{car_pk}/comments/
cars_router = routers.NestedDefaultRouter(router, r'cars', lookup='car')
cars_router.register(r'comments', CommentViewSet, basename='car-comments')

# Final URL list
urlpatterns = [
    path('', include(router.urls)),
    path('', include(cars_router.urls)),

    # Genişləndirilmiş filter endpoint
    path('cars/filter/', CarFilterView.as_view(), name='car-filter'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
