import datetime as dt
import webcolors
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Achievement, Cat, AchievementCat, CHOICES, Shelter, ShelterStaff

User = get_user_model()


class Hex2NameColor(serializers.Field):

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class AchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class ShelterStaffSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    class Meta:
        model = ShelterStaff
        fields = ('id', 'user', 'role')

    def validate(self, data):
        # Получаем приют из контекста вьюсета
        view = self.context.get('view')
        shelter = view.get_object() if view and hasattr(view, 'get_object') else data.get('shelter')
        user = data.get('user')
        
        if shelter and ShelterStaff.objects.filter(shelter=shelter, user=user).exists():
            raise serializers.ValidationError(
                "Этот пользователь уже является сотрудником данного приюта."
            )
        return data


class ShelterSerializer(serializers.ModelSerializer):
    staff = ShelterStaffSerializer(many=True, read_only=True)
    cats_count = serializers.IntegerField(source='cats.count', read_only=True)

    class Meta:
        model = Shelter
        fields = ('id', 'name', 'address', 'description', 'staff', 'cats_count')


class CatSerializer(serializers.ModelSerializer):
    achievements = AchievementSerializer(many=True, required=False)
    color = serializers.ChoiceField(choices=CHOICES)
    age = serializers.SerializerMethodField()
    owner = serializers.PrimaryKeyRelatedField(
        read_only=True,
        required=False,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Cat
        fields = (
            'id', 'name', 'color', 'birth_year',
            'achievements', 'owner', 'age', 'shelter'
        )
        read_only_fields = ('owner',)
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Cat.objects.all(),
                fields=('name', 'owner')
            )
        ]

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

    def validate_birth_year(self, value):
        year = dt.date.today().year
        if not (year - 40 < value <= year):
            raise serializers.ValidationError('Проверьте год рождения!')
        return value

    def validate(self, data):
        if data.get('color') == data.get('name'):
            raise serializers.ValidationError(
                'Имя не может совпадать с цветом!'
            )
        return data

    def create(self, validated_data):
        if 'achievements' not in self.initial_data:
            cat = Cat.objects.create(**validated_data)
            return cat

        achievements = validated_data.pop('achievements')
        cat = Cat.objects.create(**validated_data)

        for achievement in achievements:
            current_achievement, status = Achievement.objects.get_or_create(
                **achievement
            )
            AchievementCat.objects.create(
                achievement=current_achievement,
                cat=cat
            )
        return cat


class UserSerializer(serializers.ModelSerializer):
    cats = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'cats')