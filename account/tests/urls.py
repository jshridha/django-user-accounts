from django.conf.urls import include, url


urlpatterns = [
    url(r"^", include("account.urls")),
    url(r"^api", include("account.rest_urls")),
]
