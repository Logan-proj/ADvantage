from django import forms
from .models import LDAPSettings

class LDAPSettingsForm(forms.ModelForm):
    class Meta:
        model = LDAPSettings
        fields = '__all__'
        widgets = {
            'bind_password': forms.PasswordInput(),
        }


class SearchADForm(forms.Form):
    search_query = forms.CharField(label='Search AD', max_length=100)
    