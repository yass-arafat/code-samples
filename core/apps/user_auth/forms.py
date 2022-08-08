from django import forms


class UserAuthForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    widgets = {
        "new_password": forms.PasswordInput(),
        "confirm_password": forms.PasswordInput(),
    }

    def clean(self):
        cleaned_data = super(UserAuthForm, self).clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        if new_password != confirm_password:
            raise forms.ValidationError("Passwords did not match")
