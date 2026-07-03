from django.contrib import admin
from .models import Achievement, Cat, CatFamilyRelation, Shelter, ShelterStaff

admin.site.register(Cat)
admin.site.register(Achievement)
admin.site.register(Shelter)
admin.site.register(ShelterStaff)
admin.site.register(CatFamilyRelation)
