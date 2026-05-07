from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.views import View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Attempt, MailingRecipient, Message, Mailing
from .forms import RecipientForm, MessageForm, MailingForm
from django.core.cache import cache


def is_manager_or_superuser(user):
    """Вспомогательная проверка для менеджеров и суперпользователей."""
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)


# CRUD для получателей
class RecipientListView(LoginRequiredMixin, ListView):
    model = MailingRecipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'

    def get_queryset(self):
        qs = super().get_queryset()
        if is_manager_or_superuser(self.request.user):
            return qs
        return qs.filter(owner=self.request.user)


class RecipientCreateView(LoginRequiredMixin, CreateView):
    model = MailingRecipient
    form_class = RecipientForm
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = MailingRecipient
    form_class = RecipientForm
    template_name = 'mailing/recipient_form.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.owner == self.request.user


class RecipientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = MailingRecipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.owner == self.request.user


# CRUD для Сообщений
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'mailing/message_list.html'
    context_object_name = 'messages'

    def get_queryset(self):
        qs = super().get_queryset()
        if is_manager_or_superuser(self.request.user):
            return qs
        return qs.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailing/message_form.html'
    success_url = reverse_lazy('mailing:message_list')

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.owner == self.request.user


class MessageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Message
    template_name = 'mailing/message_confirm_delete.html'
    success_url = reverse_lazy('mailing:message_list')

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.owner == self.request.user


# CRUD для Рассылок
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = 'mailing/mailing_list.html'
    context_object_name = 'mailings'

    def get_queryset(self):
        qs = super().get_queryset()
        if is_manager_or_superuser(self.request.user):
            return qs
        return qs.filter(owner=self.request.user)


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = 'mailing/mailing_detail.html'
    context_object_name = 'mailing'

    def get_queryset(self):
        qs = super().get_queryset()
        if is_manager_or_superuser(self.request.user):
            return qs
        return qs.filter(owner=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()
        return obj


class MailingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailing/mailing_form.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.owner == self.request.user

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class MailingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Mailing
    template_name = 'mailing/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailing:mailing_list')

    def test_func(self):
        obj = self.get_object()
        return self.request.user.is_superuser or obj.owner == self.request.user


# Отправка рассылки
class MailingSendView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        mailing = get_object_or_404(Mailing, pk=self.kwargs['pk'])
        return self.request.user.is_superuser or mailing.owner == self.request.user

    def post(self, request, *args, **kwargs):
        mailing = get_object_or_404(Mailing, pk=self.kwargs['pk'])
        try:
            success, failure = mailing.send()
            messages.success(request, f"Рассылка завершена. Успешно: {success}, ошибок: {failure}.")
            cache.delete(f'home_stats_{mailing.owner.pk}')
            cache.delete(f'statistics_{mailing.owner.pk}')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('mailing:mailing_list')


# Главная страница
class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'mailing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cache_key = f'home_stats_{user.pk}'

        data = cache.get(cache_key)
        if data is None:
            if is_manager_or_superuser(user):
                mailings = Mailing.objects.all()
                recipients = MailingRecipient.objects.all()
            else:
                mailings = Mailing.objects.filter(owner=user)
                recipients = MailingRecipient.objects.filter(owner=user)

            data = {
                'total_mailings': mailings.count(),
                'active_mailings': mailings.filter(status=Mailing.STATUS_STARTED).count(),
                'unique_recipients': recipients.distinct().count(),
            }
            cache.set(cache_key, data, 60 * 15)  # 15 минут

        context.update(data)
        return context


class StatisticsView(LoginRequiredMixin, TemplateView):
    template_name = 'mailing/statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cache_key = f'statistics_{user.pk}'

        data = cache.get(cache_key)
        if data is None:
            if is_manager_or_superuser(user):
                attempts = Attempt.objects.all()
                total_mailings = Mailing.objects.count()
            else:
                attempts = Attempt.objects.filter(mailing__owner=user)
                total_mailings = Mailing.objects.filter(owner=user).count()

            data = {
                'total_attempts': attempts.count(),
                'successful_attempts': attempts.filter(status='success').count(),
                'failed_attempts': attempts.filter(status='failure').count(),
                'total_sent': attempts.filter(status='success').count(),
                'total_mailings': total_mailings,
            }
            cache.set(cache_key, data, 60 * 15)

        context.update(data)
        return context


# Менеджерские представления
class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'mailing/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return is_manager_or_superuser(self.request.user)

    def get_queryset(self):
        return User.objects.all()


class ToggleUserActiveView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_manager_or_superuser(self.request.user)

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = not user.is_active
        user.save()
        messages.success(request, f"Пользователь {user.email} {'заблокирован' if not user.is_active else 'разблокирован'}.")
        cache.delete(f'home_stats_{request.user.pk}')
        cache.delete(f'statistics_{request.user.pk}')
        return redirect('mailing:user_list')


class MailingDeactivateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return is_manager_or_superuser(self.request.user)

    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = Mailing.STATUS_FINISHED
        mailing.save()
        messages.success(request, f"Рассылка {mailing.pk} принудительно завершена.")
        cache.delete(f'home_stats_{mailing.owner.pk}')
        cache.delete(f'statistics_{mailing.owner.pk}')
        return redirect('mailing:mailing_list')
