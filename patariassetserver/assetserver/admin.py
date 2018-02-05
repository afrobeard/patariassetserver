from django.contrib import admin

# Register your models here.
from assetserver.models import MasterImage, DerivativeImage

admin.site.register(MasterImage)
admin.site.register(DerivativeImage)
