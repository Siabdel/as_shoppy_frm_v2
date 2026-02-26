from mapwidgets.widgets import GooglePointFieldWidget, GoogleStaticOverlayMapWidget
from django.contrib.gis.forms import PointField
from mapwidgets.widgets import MapboxPointFieldWidget

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ("coordinates", "city_hall")
        widgets = {
            'coordinates': GooglePointFieldWidget,
            'city_hall': GoogleStaticOverlayMapWidget,
        }



class HouseCreateForm(forms.ModelForm):
    location_has_default = PointField(widget=MapboxPointFieldWidget)

    class Meta:
        model = House
        fields = ("name", "location", "location_has_default")
        widgets = {
            "location": GooglePointFieldWidget,
        }