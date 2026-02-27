import string
from importlib import import_module

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import FieldDoesNotExist, ObjectDoesNotExist
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _

from core import deferred
from core.signals import customer_recognized
from core.fields import ChoiceEnum, ChoiceEnumField
from django.urls import reverse
from phonenumber_field.modelfields import PhoneNumberField
from polymorphic.models import PolymorphicModel, PolymorphicManager


SessionStore = import_module(settings.SESSION_ENGINE).SessionStore()


class CustomerState(ChoiceEnum):
    UNRECOGNIZED = 0, _("Unrecognized")
    GUEST = 1, _("Guest")
    REGISTERED = 2, ("Registered")


class CustomerQuerySet(models.QuerySet):
    def _filter_or_exclude(self, negate, *args, **kwargs):
        """
        Emulate filter queries on a Customer using attributes from the User object.
        Example: Customer.objects.filter(last_name__icontains='simpson') will return
        a queryset with customers whose last name contains "simpson".
        """
        opts = self.model._meta
        lookup_kwargs = {}
        for key, lookup in kwargs.items():
            try:
                field_name = key[:key.index('__')]
            except ValueError:
                field_name = key
            if field_name == 'pk':
                field_name = opts.pk.name
            try:
                opts.get_field(field_name)
                if isinstance(lookup, get_user_model()):
                    lookup.pk  # force lazy object to resolve
                lookup_kwargs[key] = lookup
            except FieldDoesNotExist as fdne:
                try:
                    get_user_model()._meta.get_field(field_name)
                    lookup_kwargs['user__' + key] = lookup
                except FieldDoesNotExist:
                    raise fdne
                except Exception as othex:
                    raise othex
        result = super()._filter_or_exclude(negate, *args, **lookup_kwargs)
        return result


class CustomerManager(PolymorphicManager):
    """
    Manager for the Customer database model. This manager can also cope with customers, which have
    an entity in the database but otherwise are considered as anonymous. The username of these
    so called unrecognized customers is a compact version of the session key.
    """
    BASE64_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase + '.@'
    REVERSE_ALPHABET = dict((c, i) for i, c in enumerate(BASE64_ALPHABET))
    BASE36_ALPHABET = string.digits + string.ascii_lowercase

    @classmethod
    def encode_session_key(cls, session_key):
        """
        Session keys have base 36 and length 32. Since the field ``username`` accepts only up
        to 30 characters, the session key is converted to a base 64 representation, resulting
        in a length of approximately 28.
        """
        return cls._encode(int(session_key[:32], 36), cls.BASE64_ALPHABET)

    @classmethod
    def decode_session_key(cls, compact_session_key):
        """
        Decode a compact session key back to its original length and base.
        """
        base_length = len(cls.BASE64_ALPHABET)
        n = 0
        for c in compact_session_key:
            n = n * base_length + cls.REVERSE_ALPHABET[c]
        return cls._encode(n, cls.BASE36_ALPHABET).zfill(32)

    @classmethod
    def _encode(cls, n, base_alphabet):
        base_length = len(base_alphabet)
        s = []
        while True:
            n, r = divmod(n, base_length)
            s.append(base_alphabet[r])
            if n == 0:
                break
        return ''.join(reversed(s))

    def get_queryset(self):
        """
        Whenever we fetch from the Customer table, inner join with the User table to reduce the
        number of presumed future queries to the database.
        """
        qs = self._queryset_class(self.model, using=self._db).select_related('user')
        return qs

    def create(self, *args, **kwargs):
        if 'user' in kwargs and kwargs['user'].is_authenticated:
            kwargs.setdefault('recognized', CustomerState.REGISTERED)
        customer = super().create(*args, **kwargs)
        return customer

   
   
class BaseCustomer(models.Model, metaclass=deferred.ForeignKeyBuilder):
    """
    Base class for shop customers.
    """

    recognized = ChoiceEnumField(
        _("Recognized as"),
        enum_type=CustomerState,
        help_text=_("Designates the state the customer is recognized as."),
    )

    last_access = models.DateTimeField(
        _("Last accessed"),
        default=timezone.now,
    )

    extra = models.JSONField(
        editable=False,
        verbose_name=_("Extra information about this customer"),
        null=True, blank=True
    )

    objects = CustomerManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_username()

  
  
    @property
    def is_anonymous(self):
        return self.recognized in (CustomerState.UNRECOGNIZED, CustomerState.GUEST)

    @property
    def is_authenticated(self):
        return self.recognized is CustomerState.REGISTERED

    @property
    def is_recognized(self):
        """
        Return True if the customer is associated with a User account.
        Unrecognized customers have accessed the shop, but did not register
        an account nor declared themselves as guests.
        """
        return self.recognized is not CustomerState.UNRECOGNIZED

    @property
    def is_guest(self):
        """
        Return true if the customer isn't associated with valid User account, but declared
        himself as a guest, leaving their email address.
        """
        return self.recognized is CustomerState.GUEST

    def recognize_as_guest(self, request=None, commit=True):
        """
        Recognize the current customer as guest customer.
        """
        if self.recognized != CustomerState.GUEST:
            self.recognized = CustomerState.GUEST
            if commit:
                self.save(update_fields=['recognized'])
            customer_recognized.send(sender=self.__class__, customer=self, request=request)

    @property
    def is_registered(self):
        """
        Return true if the customer has registered himself.
        """
        return self.recognized is CustomerState.REGISTERED

    def recognize_as_registered(self, request=None, commit=True):
        """
        Recognize the current customer as registered customer.
        """
        if self.recognized != CustomerState.REGISTERED:
            self.recognized = CustomerState.REGISTERED
            if commit:
                self.save(update_fields=['recognized'])
            customer_recognized.send(sender=self.__class__, customer=self, request=request)

    @property
    def is_visitor(self):
        """
        Always False for instantiated Customer objects.
        """
        return False

   

    def get_or_assign_number(self):
        """
        Hook to get or to assign the customers number. It is invoked, every time an Order object
        is created. Using a customer number, which is different from the primary key is useful for
        merchants, wishing to assign sequential numbers only to customers which actually bought
        something. Otherwise the customer number (primary key) is increased whenever a site visitor
        puts something into the cart. If he never proceeds to checkout, that entity expires and may
        be deleted at any time in the future.
        """
        return self.get_number()

    def save(self, **kwargs):
        super().save(**kwargs)


class Customer(PolymorphicModel):
    code = models.CharField(max_length=50, unique=True, editable=False)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,)
    created_at = models.DateField(auto_now_add=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField()
    company = models.CharField(max_length=100, blank=True, null=True)
    address1 = models.CharField(max_length=100)
    address2 = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    company_logo = models.ImageField(blank=True)
    phone_number = PhoneNumberField(blank=True)
    
    class Meta:
        ordering = ('first_name', 'last_name', )
        verbose_name = "Customer"
        verbose_name_plural = "Customers"  # client
        unique_together = [('email', ), ('email', 'first_name', 'last_name' ),]
        app_label = 'customer'

    def __str__(self):
        return f"{self.code}-{self.first_name} {self.last_name}"
    
    #@property 
    def get_absolute_url(self):
        return reverse("customer:client-edit", kwargs={"pk": self.pk})

    def __repr__(self):
        return f"Custom: {self.first_name} {self.last_name}"

    def generate_invoice_number(self):
        today = timezone.now()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")

        # Générer le numéro de facture
        # Nous utilisons self.pk pour l'ID de la facture, qui sera disponible après la sauvegarde initiale
        new_code = f"CLI-{year}{month}{day}-00{self.pk:06d}"
        return new_code

    def save(self, *args, **kwargs):
        # Sauvegarder d'abord pour obtenir un ID (self.pk)
        super().save(*args, **kwargs)
        
        # Générer et sauvegarder le numéro de facture si ce n'est pas déjà fait
        if not self.code:
            self.code = self.generate_invoice_number()
            super().save(update_fields=['code'])


class VisitingCustomer:
    """
    This dummy object is used for customers which just visit the site. Whenever a VisitingCustomer
    adds something to the cart, this object is replaced against a real Customer object.
    """
    user = AnonymousUser()

    def __str__(self):
        return 'Visitor'

    @property
    def email(self):
        return ''

    @email.setter
    def email(self, value):
        pass

    @property
    def is_anonymous(self):
        return True

    @property
    def is_authenticated(self):
        return False

    @property
    def is_recognized(self):
        return False

    @property
    def is_guest(self):
        return False

    @property
    def is_registered(self):
        return False

    @property
    def is_visitor(self):
        return True

    def save(self, **kwargs):
        pass


@receiver(user_logged_in)
def handle_customer_login(sender, **kwargs):
    """
    Update request.customer to an authenticated Customer
    """
    try:
        kwargs['request'].customer = kwargs['user'].customer
    except (AttributeError, ObjectDoesNotExist):
        kwargs['request'].customer = SimpleLazyObject(lambda: Customer.objects.get_from_request(kwargs['request']))


@receiver(user_logged_out)
def handle_customer_logout(sender, **kwargs):
    """
    Update request.customer to a visiting Customer
    """
    # defer assignment to anonymous customer, since the session_key is not yet rotated
    kwargs['request'].customer = SimpleLazyObject(lambda: Customer.objects.get_from_request(kwargs['request']))


# model de prise de RDV
class Appointment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    purpose = models.CharField(max_length=200)
    
    class Meta:
        app_label = 'customer'
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ['date_time']
    
    def __str__(self):
        return f"Appointment {self.id} - {self.customer} - {self.date_time}"
