import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger(__name__)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_manager = models.BooleanField(default=False, verbose_name="Менеджер")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"{self.user.email} ({'Менеджер' if self.is_manager else 'Пользователь'})"


class MailingRecipient(models.Model):
    email = models.EmailField(unique=True, max_length=254, verbose_name="Email")
    full_name = models.CharField(max_length=100, verbose_name="Ф.И.О")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
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
        ordering = ["-created_at"]

    def __str__(self):
        return self.topic or "(без темы)"


class Mailing(models.Model):
    STATUS_CREATED = "created"
    STATUS_STARTED = "started"
    STATUS_FINISHED = "finished"
    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_STARTED, "Запущена"),
        (STATUS_FINISHED, "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время начала")

    end_time = models.DateTimeField(verbose_name="Дата и время окончания")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус")
    message = models.ForeignKey("Message", on_delete=models.PROTECT, verbose_name="Сообщение")
    recipients = models.ManyToManyField(MailingRecipient, verbose_name="Получатели")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_time"]

    def clean(self):
        """Валидация на уровне модели."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Дата начала должна быть раньше даты окончания.")
        if not self.pk and self.start_time and self.start_time < timezone.now():
            raise ValidationError("Дата начала не может быть в прошлом.")

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
            self.save(update_fields=["status"])

    @property
    def status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def __str__(self):
        return f"Рассылка от {self.start_time} ({self.status_display})"

    def send(self):
        """Отправляет рассылку всем получателям, создавая записи Attempt пакетно."""
        now = timezone.now()
        if now < self.start_time:
            raise ValueError("Рассылка ещё не началась.")
        if now > self.end_time:
            raise ValueError("Время рассылки истекло.")

        self.update_status()
        if self.status != self.STATUS_STARTED:
            raise ValueError(f"Рассылка не может быть отправлена. Текущий статус: {self.get_status_display()}")

        recipients = self.recipients.all()
        if not recipients.exists():
            raise ValueError("Нет получателей для отправки.")

        attempts = []
        success_count = 0
        failure_count = 0

        for recipient in recipients:
            try:
                send_mail(
                    subject=self.message.topic,
                    message=self.message.body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                attempts.append(Attempt(mailing=self, status="success", server_response="OK"))
                success_count += 1
            except Exception as e:
                attempts.append(Attempt(mailing=self, status="failure", server_response=str(e)))
                failure_count += 1
                logger.error(f"Ошибка отправки письма для {recipient.email}: {e}")

        # Пакетное создание всех попыток одним запросом
        if attempts:
            Attempt.objects.bulk_create(attempts)

        return success_count, failure_count


class Attempt(models.Model):
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE, related_name="attempts")
    attempt_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=[("success", "Успешно"), ("failure", "Не успешно")], verbose_name="Статус попытки"
    )
    server_response = models.TextField(blank=True, verbose_name="Ответ сервера")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
