from django.test import TestCase

# Create your tests here.

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Quote, Client
from .forms import QuoteForm
from datetime import date, timedelta

class QuoteModelTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(nom="Test Client")
        self.quote = Quote.objects.create(
            client=self.client,
            date_expiration=date.today() + timedelta(days=30),
            montant_total=1000.00,
            statut='brouillon',
            description="Test Quote"
        )

    def test_quote_creation(self):
        self.assertTrue(isinstance(self.quote, Quote))
        self.assertEqual(self.quote.__str__(), f"Devis {self.quote.numero}")

    def test_quote_number_generation(self):
        self.assertTrue(self.quote.numero.startswith("QUO-"))

    def test_quote_status_change(self):
        self.quote.marquer_comme_envoye()
        self.assertEqual(self.quote.statut, 'envoyé')

class QuoteFormTest(TestCase):
    def setUp(self):
        self.client = Client.objects.create(nom="Test Client")

    def test_valid_form(self):
        data = {
            'client': self.client.id,
            'date_expiration': date.today() + timedelta(days=30),
            'montant_total': 1000.00,
            'statut': 'brouillon',
            'description': "Test Quote"
        }
        form = QuoteForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        data = {
            'client': self.client.id,
            'date_expiration': date.today() + timedelta(days=30),
            'montant_total': -1000.00,  # Invalid negative amount
            'statut': 'brouillon',
            'description': "Test Quote"
        }
        form = QuoteForm(data=data)
        self.assertFalse(form.is_valid())

class QuoteViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.client_obj = Client.objects.create(nom="Test Client")
        self.quote = Quote.objects.create(
            client=self.client_obj,
            date_expiration=date.today() + timedelta(days=30),
            montant_total=1000.00,
            statut='brouillon',
            description="Test Quote"
        )

    def test_quote_list_view(self):
        response = self.client.get(reverse('quotes:quote_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.quote.numero)

    def test_quote_detail_view(self):
        response = self.client.get(reverse('quotes:quote_detail', args=[self.quote.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.quote.numero)

    def test_quote_create_view(self):
        response = self.client.post(reverse('quotes:quote_create'), {
            'client': self.client_obj.id,
            'date_expiration': date.today() + timedelta(days=30),
            'montant_total': 2000.00,
            'statut': 'brouillon',
            'description': "New Test Quote"
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful creation
        self.assertEqual(Quote.objects.count(), 2)

    def test_quote_update_view(self):
        response = self.client.post(reverse('quotes:quote_update', args=[self.quote.id]), {
            'client': self.client_obj.id,
            'date_expiration': date.today() + timedelta(days=60),
            'montant_total': 1500.00,
            'statut': 'envoyé',
            'description': "Updated Test Quote"
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        self.quote.refresh_from_db()
        self.assertEqual(self.quote.montant_total, 1500.00)
        self.assertEqual(self.quote.statut, 'envoyé')

class QuoteAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)
        self.client_obj = Client.objects.create(nom="Test Client")
        self.quote_data = {
            'client': self.client_obj.id,
            'date_expiration': (date.today() + timedelta(days=30)).isoformat(),
            'montant_total': 1000.00,
            'statut': 'brouillon',
            'description': "Test Quote"
        }

    def test_create_quote(self):
        response = self.client.post(reverse('quote-list'), self.quote_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quote.objects.count(), 1)

    def test_read_quote(self):
        quote = Quote.objects.create(**self.quote_data)
        response = self.client.get(reverse('quote-detail', args=[quote.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['numero'], quote.numero)

    def test_update_quote(self):
        quote = Quote.objects.create(**self.quote_data)
        updated_data = self.quote_data.copy()
        updated_data['montant_total'] = 1500.00
        response = self.client.put(reverse('quote-detail', args=[quote.id]), updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Quote.objects.get(id=quote.id).montant_total, 1500.00)

    def test_delete_quote(self):
        quote = Quote.objects.create(**self.quote_data)
        response = self.client.delete(reverse('quote-detail', args=[quote.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Quote.objects.count(), 0)

    def test_convert_quote_to_invoice(self):
        quote = Quote.objects.create(**self.quote_data)
        quote.statut = 'accepté'
        quote.save()
        response = self.client.post(reverse('quote-convert-to-invoice', args=[quote.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Devis converti en facture', response.data['message'])