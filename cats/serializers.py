import datetime as dt
import webcolors
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Achievement, Cat, AchievementCat, CatFamilyRelation, CHOICES, Shelter,
    ShelterStaff
)

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


class CatShortSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year', 'age')

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year


class CatFamilyRelationSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    child_name = serializers.CharField(source='child.name', read_only=True)
    relation_label = serializers.CharField(
        source='get_relation_type_display',
        read_only=True
    )

    class Meta:
        model = CatFamilyRelation
        fields = (
            'id', 'parent', 'parent_name', 'child', 'child_name',
            'relation_type', 'relation_label', 'note', 'created_at'
        )
        read_only_fields = ('created_at',)

    def validate(self, data):
        parent = data.get(
            'parent',
            getattr(self.instance, 'parent', None)
        )
        child = data.get(
            'child',
            getattr(self.instance, 'child', None)
        )

        if parent == child:
            raise serializers.ValidationError(
                'Кот не может быть родителем самого себя.'
            )
        if parent and child and parent.birth_year >= child.birth_year:
            raise serializers.ValidationError(
                'Родитель должен быть старше ребёнка.'
            )
        if parent and child and self._creates_cycle(parent, child):
            raise serializers.ValidationError(
                'Связь создаёт цикл в семейном древе.'
            )
        return data

    def _creates_cycle(self, parent, child):
        relation_id = getattr(self.instance, 'id', None)
        stack = [child.id]
        visited = set()
        while stack:
            current_id = stack.pop()
            if current_id in visited:
                continue
            visited.add(current_id)
            if current_id == parent.id:
                return True
            relations = CatFamilyRelation.objects.filter(parent_id=current_id)
            if relation_id:
                relations = relations.exclude(id=relation_id)
            stack.extend(rel.child_id for rel in relations)
        return False


class UserSerializer(serializers.ModelSerializer):
    cats = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'cats')
