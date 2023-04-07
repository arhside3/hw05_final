from django.urls import path

from posts import views

app_name = '%(app_label)s'

urlpatterns = [
    path('create/', views.create_post, name='create_post'),
    path('group/<slug:slug>/', views.group_posts, name='group_posts'),
    path('', views.index, name='index_name'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('posts/<int:pk>/edit/', views.post_edit, name='update_post'),
    path('posts/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('follow/', views.follow_index, name='follow_index'),
    path(
        'profile/<str:username>/follow/',
        views.profile_follow,
        name='profile_follow',
    ),
    path(
        'profile/<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow',
    ),
]
