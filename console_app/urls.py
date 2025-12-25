from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('user/me/', views.user_me_view, name='user_me'),
    path('user/me/portrait/', views.get_user_me_portrait, name='user_me_portrait'),
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.logout, name='logout'),
    path('oauth2/callback/', views.oauth2_callback, name='oauth2_callback'),
    path('oauth2/login/', views.oauth2_login, name='oauth2_login'),
    path('avatars/', views.AvatarsView.as_view(), name='avatars'),
    path('avatars/<uuid:avatar_id>/', views.AvatarDetailView.as_view(), name='avatar_detail'),
    path('seminars/', views.SeminarsView.as_view(), name='seminars'),
    path('seminars/<uuid:seminar_id>/', views.SeminarDetailView.as_view(), name='seminar_detail'),
    path('speakers/', views.SpeakersView.as_view(), name='speakers'),
    path('speakers/<uuid:speaker_id>/', views.SpeakerDetailView.as_view(), name='speaker_detail'),
    path('voices/', views.VoicesView.as_view(), name='voices'),
    path('generation_orders/', views.GenerationOrdersView.as_view(), name='generation_orders'),
]

