from django.urls import path

from . import views

app_name = "mailing"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/toggle-active/", views.ToggleUserActiveView.as_view(), name="toggle_user_active"),
    path("users/<int:pk>/toggle-manager/", views.ToggleManagerStatusView.as_view(), name="toggle_manager"),
    path("mailings/<int:pk>/deactivate/", views.MailingDeactivateView.as_view(), name="mailing_deactivate"),
    # Получатели
    path("recipients/", views.RecipientListView.as_view(), name="recipient_list"),
    path("recipients/create/", views.RecipientCreateView.as_view(), name="recipient_create"),
    path("recipients/<int:pk>/update/", views.RecipientUpdateView.as_view(), name="recipient_update"),
    path("recipients/<int:pk>/delete/", views.RecipientDeleteView.as_view(), name="recipient_delete"),
    # Сообщения
    path("messages/", views.MessageListView.as_view(), name="message_list"),
    path("messages/create/", views.MessageCreateView.as_view(), name="message_create"),
    path("messages/<int:pk>/update/", views.MessageUpdateView.as_view(), name="message_update"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_delete"),
    # Рассылка
    path("mailings/", views.MailingListView.as_view(), name="mailing_list"),
    path("mailings/create/", views.MailingCreateView.as_view(), name="mailing_create"),
    path("mailings/<int:pk>/", views.MailingDetailView.as_view(), name="mailing_detail"),
    path("mailings/<int:pk>/update/", views.MailingUpdateView.as_view(), name="mailing_update"),
    path("mailings/<int:pk>/delete/", views.MailingDeleteView.as_view(), name="mailing_delete"),
    # Отправка
    path("mailings/<int:pk>/send/", views.MailingSendView.as_view(), name="mailing_send"),
]
