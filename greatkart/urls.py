from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import static, staticfiles_urlpatterns
from . import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('store/', include('store.urls')),
    path('cart/', include('carts.urls')),
    path('accounts/', include('accounts.urls')),
    path('orders/', include('orders.urls')),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)