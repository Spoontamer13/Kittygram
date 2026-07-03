from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Cat

User = get_user_model()


class CatFamilyTreeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='yarik',
            password='strong-test-password'
        )
        self.client.force_authenticate(self.user)
        self.mother = Cat.objects.create(
            name='Marta',
            color='White',
            birth_year=2017,
            owner=self.user
        )
        self.father = Cat.objects.create(
            name='Bars',
            color='Black',
            birth_year=2016,
            owner=self.user
        )
        self.kitten = Cat.objects.create(
            name='Murka',
            color='Gray',
            birth_year=2022,
            owner=self.user
        )

    def test_create_family_relation(self):
        response = self.client.post('/api/cat-family-relations/', {
            'parent': self.mother.id,
            'child': self.kitten.id,
            'relation_type': 'mother',
            'note': 'Основная линия семейного древа',
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent_name'], 'Marta')
        self.assertEqual(response.data['child_name'], 'Murka')

    def test_family_tree_contains_parents(self):
        self.client.post('/api/cat-family-relations/', {
            'parent': self.mother.id,
            'child': self.kitten.id,
            'relation_type': 'mother',
        })
        self.client.post('/api/cat-family-relations/', {
            'parent': self.father.id,
            'child': self.kitten.id,
            'relation_type': 'father',
        })

        response = self.client.get(
            f'/api/cats/{self.kitten.id}/family-tree/'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cat']['name'], 'Murka')
        self.assertEqual(len(response.data['parents']), 2)
        self.assertEqual(len(response.data['ancestors']), 2)

    def test_parent_must_be_older_than_child(self):
        response = self.client.post('/api/cat-family-relations/', {
            'parent': self.kitten.id,
            'child': self.mother.id,
            'relation_type': 'mother',
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Родитель должен быть старше ребёнка.', str(response.data))
