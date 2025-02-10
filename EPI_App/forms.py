from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile, ProductScheme, Payment

class SignupForm(forms.ModelForm):
    accept_terms = forms.BooleanField(
        required=True,
        label="I accept the Terms and Conditions.",
        error_messages={'required': "You must accept the terms and conditions to register."},
    )
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'placeholder': 'Enter username', 'class': 'form-control'}),
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'placeholder': 'Enter email', 'class': 'form-control'}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter password', 'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password', 'class': 'form-control'}),
    )
    kyc_document = forms.FileField(
        required=True,
        label="Upload KYC Document",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )
    kyc_document_type = forms.ChoiceField(
        required=True,
        label="Document Type",
        choices=[
            ('passport', 'Passport'),
            ('aadhaar', 'Aadhaar Card'),
            ('license', 'Driver’s License'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    pan_card = forms.FileField(
        required=True,
        label="Upload PAN Card",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )
    bank_passbook = forms.FileField(
        required=True,
        label="Upload Bank Passbook",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )
    profile_photo = forms.FileField(
        required=True,
        label="Upload Profie",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise ValidationError("Passwords do not match.")
        return password2

    def clean_kyc_document(self):
        document = self.cleaned_data.get('kyc_document')
        if document:
            if document.size > 5 * 1024 * 1024:  # Limit size to 5MB
                raise ValidationError("Document size cannot exceed 5MB.")
            if not document.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
        return document

    def clean_pan_card(self):
        pan_card = self.cleaned_data.get('pan_card')
        if pan_card:
            if pan_card.size > 5 * 1024 * 1024:  # Limit size to 5MB
                raise ValidationError("PAN card size cannot exceed 5MB.")
            if not pan_card.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
        return pan_card

    def clean_bank_passbook(self):
        bank_passbook = self.cleaned_data.get('bank_passbook')
        if bank_passbook:
            if bank_passbook.size > 5 * 1024 * 1024:  # Limit size to 5MB
                raise ValidationError("Bank passbook size cannot exceed 5MB.")
            if not bank_passbook.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise ValidationError("Only PDF, JPG, JPEG, and PNG files are allowed.")
        return bank_passbook
    
    def clean_profile_photo(self):
        profile_photo = self.cleaned_data.get('profile_photo')
        if profile_photo:
            # Limit the size to 1GB (1GB = 1024 * 1024 * 1024 bytes)
            if profile_photo.size > 1 * 1024 * 1024 * 1024:  # 1GB
                raise ValidationError("Profile photo size cannot exceed 1GB.")
            
            # Allow only specific file types: JPG, JPEG, PNG
            if not profile_photo.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise ValidationError("Only JPG, JPEG, and PNG files are allowed for profile photo.")
        
        return profile_photo

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_photo','kyc_document_type', 'kyc_document', 'pan_card', 'bank_passbook']

class ProductSchemeForm(forms.ModelForm):
    class Meta:
        model = ProductScheme
        fields = ['product_id', 'investment', 'days']
        widgets = {
            'product_id': forms.TextInput(attrs={'readonly': True}),
            'days': forms.TextInput(attrs={'readonly': True}),
            }
    
    def __init__(self, *args, **kwargs):
        super(ProductSchemeForm, self).__init__(*args, **kwargs)
        # Automatically set the 'profile' field to the currently logged-in user's profile
        if 'profile' not in self.initial:
            self.initial['profile'] = kwargs.get('instance').profile if kwargs.get('instance') else None

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['product_scheme', 'transaction_id', 'payment_proof']
    
    def __init__(self, *args, **kwargs):
        # Get the user from the kwargs
        user = kwargs.pop('user', None)  # This removes the 'user' key from kwargs
        super().__init__(*args, **kwargs)
        if user:
            # Filter product schemes by the logged-in user's profile
            self.fields['product_scheme'].queryset = ProductScheme.objects.filter(profile=user.profile)