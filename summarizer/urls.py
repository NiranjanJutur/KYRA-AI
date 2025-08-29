from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    path('', views.upload_pdf, name='upload_pdf'),
    path('pdfs/', views.PDFListView.as_view(), name='pdf_list'),
    path('images/', views.ImageListView.as_view(), name='image_list'),
    path('pdfs/<int:pk>/', views.pdf_detail, name='pdf_detail'),
    path('pdfs/<int:pk>/update_language/', views.update_language, name='update_language'),
    path('pdfs/<int:pk>/text_to_speech/', views.text_to_speech_view, name='text_to_speech'),
    path('pdf/translation_status/<str:task_id>/', views.check_translation_status, name='check_translation_status'),
    path('pdf/<int:pk>/delete/', views.delete_pdf, name='delete_pdf'),
    path('pdf/<int:pk>/download/', views.download_pdf, name='download_pdf'),
    path('pdfs/<int:pk>/ask/', views.ask_question, name='ask_question'),
    path('pdfs/<int:pk>/regenerate_summary/', views.regenerate_summary, name='regenerate_summary'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),
    # path('images/<int:pk>/update-language/', views.update_image_language, name='update_image_language'),
    path('images/upload/', views.upload_image, name='upload_image'),
    path('images/<int:pk>/', views.image_detail, name='image_detail'),
    path('images/<int:pk>/ask/', views.ask_image_question, name='ask_image_question'),
    path('images/<int:pk>/delete/', views.delete_image, name='delete_image'),
    path('images/<int:pk>/download/', views.download_image, name='download_image'),
    path('images/<int:pk>/update_language/', views.update_image_language, name='update_image_language'),
    path('images/<int:pk>/text_to_speech/', views.image_text_to_speech, name='image_text_to_speech'),
    path('tesseract-installation/', views.tesseract_installation, name='tesseract_installation'),
    path('profile/', views.profile, name='profile'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('update_language_preference/', views.update_language_preference, name='update_language_preference'),
]