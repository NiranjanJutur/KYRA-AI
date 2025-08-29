from django import forms
from .models import PDFDocument, ImageDocument, UserProfile

class PDFUploadForm(forms.ModelForm):
    class Meta:
        model = PDFDocument
        fields = ['file', 'summary_type']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'application/pdf',
                'aria-label': 'Upload PDF file',
                'aria-describedby': 'fileHelp'
            }),
            'summary_type': forms.Select(attrs={
                'class': 'form-control',
                'aria-label': 'Select summary type'
            })
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if not file.name.endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed.')
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError('File size cannot exceed 10MB.')
        return file


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = ImageDocument
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'aria-label': 'Upload image file',
                'aria-describedby': 'imageFileHelp'
            })
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Image size cannot exceed 5MB.')
        return image


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'company_name', 'job_title', 'website']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'aria-label': 'Upload profile picture'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your company name'
            }),
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your job title'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            })
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 2 * 1024 * 1024:  # 2MB limit
                raise forms.ValidationError('Profile picture size cannot exceed 2MB.')
        return avatar