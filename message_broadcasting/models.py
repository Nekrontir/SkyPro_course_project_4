from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.

class MailingRecipient(models.Model):
    email = models.EmailField(unique=True, max_length=254, verbose_name= "Email")
    full_name = models.CharField(max_length=100, verbose_name= "Ф.И.О")
    comment = models.TextField(blank=True, verbose_name= "Комментарий")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class Message(models.Model):
    topic = models.CharField(max_length=100, verbose_name="Тема письма")
    body = models.TextField(blank=True, verbose_name="Тело письма")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['-created_at']

    def __str__(self):
        return self.topic or "(без темы)"


class Mailing(models.Model):
    STATUS_CREATED = 'created'
    STATUS_STARTED = 'started'
    STATUS_FINISHED = 'finished'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_STARTED, 'Запущена'),
        (STATUS_FINISHED, 'Завершена'),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name="Статус"
    )
    message = models.ForeignKey(
        'Message',
        on_delete=models.PROTECT,
        verbose_name="Сообщение"
    )
    recipients = models.ManyToManyField(MailingRecipient, verbose_name="Получатели")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ['-start_time']

    def clean(self):
        """Валидация на уровне модели."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError('Дата начала должна быть раньше даты окончания.')
        if not self.pk and self.start_time and self.start_time < timezone.now():
            raise ValidationError('Дата начала не может быть в прошлом.')

    def update_status(self):
        """Пересчитывает и сохраняет статус, если он изменился."""
        now = timezone.now()
        new_status = self.STATUS_CREATED
        if self.start_time <= now <= self.end_time:
            new_status = self.STATUS_STARTED
        elif now > self.end_time:
            new_status = self.STATUS_FINISHED

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def __str__(self):
        return f"Рассылка от {self.start_time} ({self.status_display})"

class Attempt(models.Model):
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name='attempts')
    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('success', 'Успешно'), ('failure', 'Не успешно')],
        verbose_name="Статус попытки"
    )
server_response = models.TextField(blank=True, verbose_name="Ответ сервера")