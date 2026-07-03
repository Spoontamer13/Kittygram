from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

CHOICES = (
    ('Gray', 'Серый'),
    ('Black', 'Чёрный'),
    ('White', 'Белый'),
    ('Ginger', 'Рыжий'),
    ('Mixed', 'Смешанный'),
)


class Achievement(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Shelter(models.Model):
    name = models.CharField(max_length=128)
    address = models.CharField(max_length=256)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ShelterStaff(models.Model):
    ROLE_CHOICES = (
        ('manager', 'Менеджер'),
        ('volunteer', 'Волонтер'),
        ('vet', 'Ветеринар'),
    )
    shelter = models.ForeignKey(
        Shelter,
        related_name='staff',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        related_name='shelter_roles',
        on_delete=models.CASCADE
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['shelter', 'user'],
                name='unique_shelter_user'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.role} in {self.shelter.name}'


class Cat(models.Model):
    name = models.CharField(max_length=16)
    color = models.CharField(max_length=16, choices=CHOICES)
    birth_year = models.IntegerField()
    owner = models.ForeignKey(
        User,
        related_name='cats',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    achievements = models.ManyToManyField(
        Achievement,
        through='AchievementCat'
    )
    shelter = models.ForeignKey(
        Shelter,
        related_name='cats',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'owner'],
                name='unique_name_owner'
            )
        ]

    def __str__(self):
        return self.name


class AchievementCat(models.Model):
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    cat = models.ForeignKey(Cat, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.achievement} {self.cat}'


class CatFamilyRelation(models.Model):
    RELATION_CHOICES = (
        ('mother', 'Мать'),
        ('father', 'Отец'),
        ('parent', 'Родитель'),
        ('guardian', 'Опекун'),
    )

    parent = models.ForeignKey(
        Cat,
        related_name='children_relations',
        on_delete=models.CASCADE
    )
    child = models.ForeignKey(
        Cat,
        related_name='parent_relations',
        on_delete=models.CASCADE
    )
    relation_type = models.CharField(
        max_length=16,
        choices=RELATION_CHOICES,
        default='parent'
    )
    note = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('parent', 'child'),
                name='unique_cat_parent_child'
            ),
        ]
        ordering = ('parent__name', 'child__name')

    def __str__(self):
        return f'{self.parent.name} -> {self.child.name}'
