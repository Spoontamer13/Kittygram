from django.contrib import admin
from .models import Cat, Achievement, Shelter, ShelterStaff

admin.site.register(Cat)
admin.site.register(Achievement)
admin.site.register(Shelter)
admin.site.register(ShelterStaff)
