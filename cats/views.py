from rest_framework import (
    viewsets, mixins, serializers, filters, permissions, status
)
from rest_framework.throttling import ScopedRateThrottle
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.decorators import action
from rest_framework.response import Response
from .models import (
    Achievement, Cat, CatFamilyRelation, User, CHOICES, Shelter, ShelterStaff
)
from .serializers import (
    AchievementSerializer, CatFamilyRelationSerializer, CatSerializer,
    CatShortSerializer, UserSerializer, ShelterSerializer, ShelterStaffSerializer
)
from .permissions import OwnerOrReadOnly, ReadOnly, IsShelterStaffOrReadOnly
from .throttling import WorkingHoursRateThrottle
from .pagination import CatsPagination


class CatListSerializer(serializers.ModelSerializer):
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color')


class CatViewSet(viewsets.ModelViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer
    throttle_classes = (WorkingHoursRateThrottle, ScopedRateThrottle)
    throttle_scope = 'low_request'
    pagination_class = CatsPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter)
    filterset_fields = ('color', 'birth_year')
    search_fields = ('name',)
    ordering_fields = ('name', 'birth_year')
    ordering = ('birth_year',)

    def perform_create(self, serializer):
        if self.request.data.get('shelter'):
            serializer.save()
        else:
            serializer.save(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == 'list':
            return CatListSerializer
        return CatSerializer

    def get_permissions(self):
        if self.action in (
            'retrieve', 'family_tree', 'ancestors', 'descendants'
        ):
            return (ReadOnly(),)
        return (OwnerOrReadOnly(),)

    @action(detail=False, url_path='recent-white-cats')
    def recent_white_cats(self, request):
        cats = Cat.objects.filter(color='White')[:5]
        serializer = self.get_serializer(cats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='family-tree')
    def family_tree(self, request, pk=None):
        cat = self.get_object()
        parent_relations = CatFamilyRelation.objects.filter(
            child=cat
        ).select_related('parent', 'child')
        child_relations = CatFamilyRelation.objects.filter(
            parent=cat
        ).select_related('parent', 'child')
        siblings = Cat.objects.filter(
            parent_relations__parent__children_relations__child=cat
        ).exclude(id=cat.id).distinct()
        return Response({
            'cat': CatShortSerializer(cat).data,
            'parents': CatFamilyRelationSerializer(
                parent_relations,
                many=True
            ).data,
            'children': CatFamilyRelationSerializer(
                child_relations,
                many=True
            ).data,
            'siblings': CatShortSerializer(siblings, many=True).data,
            'ancestors': self._collect_relatives(cat, 'ancestors'),
            'descendants': self._collect_relatives(cat, 'descendants'),
        })

    @action(detail=True, methods=['get'], url_path='ancestors')
    def ancestors(self, request, pk=None):
        return Response(
            self._collect_relatives(self.get_object(), 'ancestors')
        )

    @action(detail=True, methods=['get'], url_path='descendants')
    def descendants(self, request, pk=None):
        return Response(
            self._collect_relatives(self.get_object(), 'descendants')
        )

    def _collect_relatives(self, cat, direction, depth=0, visited=None):
        if visited is None:
            visited = set()
        if cat.id in visited:
            return []
        visited.add(cat.id)

        if direction == 'ancestors':
            relations = CatFamilyRelation.objects.filter(
                child=cat
            ).select_related('parent')
            relative_attr = 'parent'
        else:
            relations = CatFamilyRelation.objects.filter(
                parent=cat
            ).select_related('child')
            relative_attr = 'child'

        relatives = []
        for relation in relations:
            relative = getattr(relation, relative_attr)
            relatives.append({
                'id': relative.id,
                'name': relative.name,
                'color': relative.color,
                'birth_year': relative.birth_year,
                'depth': depth + 1,
                'relation_type': relation.relation_type,
                'relation_label': relation.get_relation_type_display(),
                'relatives': self._collect_relatives(
                    relative,
                    direction,
                    depth + 1,
                    visited.copy()
                ),
            })
        return relatives


class CatFamilyRelationViewSet(viewsets.ModelViewSet):
    queryset = CatFamilyRelation.objects.select_related('parent', 'child')
    serializer_class = CatFamilyRelationSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = CatsPagination
    filter_backends = (
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    )
    filterset_fields = ('parent', 'child', 'relation_type')
    search_fields = ('parent__name', 'child__name', 'note')
    ordering_fields = ('created_at', 'relation_type', 'parent__name')
    ordering = ('parent__name', 'child__name')


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer


class CreateRetrieveViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    pass


class LightCatViewSet(CreateRetrieveViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer


class ShelterViewSet(viewsets.ModelViewSet):
    queryset = Shelter.objects.all()
    serializer_class = ShelterSerializer
    permission_classes = (IsShelterStaffOrReadOnly,)
    pagination_class = CatsPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'address')

    def perform_create(self, serializer):
        shelter = serializer.save()
        ShelterStaff.objects.create(
            shelter=shelter,
            user=self.request.user,
            role='manager'
        )

    @action(detail=True, methods=['post'], url_path='add-staff')
    def add_staff(self, request, pk=None):
        shelter = self.get_object()
        serializer = ShelterStaffSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save(shelter=shelter)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {"detail": "Этот пользователь уже является сотрудником данного приюта."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def cats(self, request, pk=None):
        shelter = self.get_object()
        cats = shelter.cats.all()
        serializer = CatSerializer(cats, many=True)
        return Response(serializer.data)
