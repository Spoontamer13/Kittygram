from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from cats.views import (
    CatFamilyRelationViewSet, CatViewSet, UserViewSet, AchievementViewSet,
    LightCatViewSet, ShelterViewSet
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

router = DefaultRouter()
router.register('cats', CatViewSet)
router.register('users', UserViewSet)
router.register('achievements', AchievementViewSet)
router.register('mycats', LightCatViewSet)
router.register('shelters', ShelterViewSet)
router.register('cat-family-relations', CatFamilyRelationViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
