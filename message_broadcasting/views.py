from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import MailingRecipient
from .forms import RecipientForm

# Create your views here.

class RecipientListView(LoginRequiredMixin, ListView):
    model = MailingRecipient
    template_name = 'mailing/recipient_list.html'
    context_object_name = 'recipients'

    def get_queryset(self):
        return MailingRecipient.objects.filter(owner=self.request.user)

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
        return obj.owner == self.request.user

class RecipientDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = MailingRecipient
    template_name = 'mailing/recipient_confirm_delete.html'
    success_url = reverse_lazy('mailing:recipient_list')

    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user