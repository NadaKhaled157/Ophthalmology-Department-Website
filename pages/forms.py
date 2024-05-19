from django import forms

class UserInputForm(forms.Form):
    user_data = forms.CharField(label='Enter Data')
