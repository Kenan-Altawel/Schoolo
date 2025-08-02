from django.db import models
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel, User
from django.utils.translation import gettext_lazy as _
from teachers.models import Teacher
from subject.models import Subject
from classes.models import Section
from academic.models import AcademicTerm,AcademicYear
class SubjectContent(AutoCreateAndAutoUpdateTimeStampedModel):
    

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='contents',
        verbose_name=_("المادة الدراسية")
    )
    section = models.ForeignKey(
        Section, 
        on_delete=models.CASCADE, 
        related_name='subject_contents', 
        verbose_name=_("القسم")
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_content',
        verbose_name=_("المعلم")
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("عنوان المحتوى"),
        help_text=_("عنوان وصفي للمحتوى (مثال: محاضرة 1، روابط مفيدة، ملخص الفصل الأول).")
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_contents',
        verbose_name=_("العام الدراسي")
    )
    academic_term = models.ForeignKey(
        AcademicTerm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subject_contents',
        verbose_name=_("الفصل الدراسي")
    )
    class Meta:
        verbose_name = _("محتوى المادة")
        verbose_name_plural = _("محتويات المواد")
        ordering = ['subject', 'section', 'title']

    def __str__(self):
        return f"{self.title} - {self.subject.name} [{self.section.name if self.section else 'لا يوجد قسم'}]"

   
    def clean(self):
        super().clean()
        # هنا يمكنك وضع أي تحققات أخرى تتعلق بالـ SubjectContent نفسه،
        # مثل التأكد من عدم وجود محتوى بنفس العنوان في نفس القسم/المادة.
        pass


class ContentAttachment(AutoCreateAndAutoUpdateTimeStampedModel):
    ATTACHMENT_TYPE_CHOICES = [
        ('text', _('نص')),
        ('link', _('رابط')),
        ('file', _('ملف (عام)')), # يمكن استخدامه للمستندات مثل PDF، Word
        ('image', _('صورة')),
        ('video', _('فيديو')), # <--- إضافة نوع الفيديو
        ('audio', _('صوت')),  # <--- إضافة نوع الصوت
    ]

    content = models.ForeignKey(
        SubjectContent,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_("محتوى المادة")
    )
    
    attachment_type = models.CharField(
        max_length=10,
        choices=ATTACHMENT_TYPE_CHOICES,
        verbose_name=_("نوع المرفق"),
        help_text=_("اختر نوع هذا المرفق: نص، رابط، ملف، صورة، فيديو، أو صوت.")
    )

    text_content = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("المحتوى النصي"),
        help_text=_("اكتب المحتوى النصي إذا كان نوع المرفق 'نص'.")
    )
    link_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("رابط URL"),
        help_text=_("أدخل رابط URL إذا كان نوع المرفق 'رابط'.")
    )
    file = models.FileField(
        upload_to='contents/subject_content_attachments/', 
        blank=True,
        null=True,
        verbose_name=_("ملف المرفق"),
        help_text=_("رفع ملف إذا كان نوع المرفق 'ملف'، 'صورة'، 'فيديو'، أو 'صوت'.")
    )
    
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("الوصف"),
        help_text=_("وصف قصير للمرفق.")
    )
    
    class Meta:
        verbose_name = _("مرفق المحتوى")
        verbose_name_plural = _("مرفقات المحتوى")
        ordering = ['content', 'id']

    def __str__(self):
        file_name = self.file.name.split('/')[-1] if self.file else "بلا ملف"
        if self.attachment_type == 'text' and self.text_content:
            return f"{self.content.title} - نص ({self.text_content[:50]}...)"
        elif self.attachment_type == 'link' and self.link_url:
            return f"{self.content.title} - رابط ({self.link_url})"
        elif self.attachment_type in ['file', 'image', 'video', 'audio'] and self.file:
            return f"{self.content.title} - {self.get_attachment_type_display()} ({file_name})"
        return f"{self.content.title} - مرفق غير معروف"
    
    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError

        if self.attachment_type == 'text':
            if not self.text_content:
                raise ValidationError({'text_content': _("يجب إدخال محتوى نصي إذا كان نوع المرفق 'نص'.")})
            if self.link_url or self.file:
                raise ValidationError(_("لا يمكن أن يحتوي المرفق على رابط أو ملف إذا كان نوعه 'نص'."))
        elif self.attachment_type == 'link':
            if not self.link_url:
                raise ValidationError({'link_url': _("يجب إدخال رابط URL إذا كان نوع المرفق 'رابط'.")})
            if self.text_content or self.file:
                raise ValidationError(_("لا يمكن أن يحتوي المرفق على نص أو ملف إذا كان نوعه 'رابط'."))
        elif self.attachment_type in ['file', 'image', 'video', 'audio']: 
            if not self.file:
                raise ValidationError({'file': _("يجب رفع ملف إذا كان نوع المرفق 'ملف'، 'صورة'، 'فيديو'، أو 'صوت'.")})
            if self.text_content or self.link_url:
                raise ValidationError(_("لا يمكن أن يحتوي المرفق على نص أو رابط إذا كان نوعه 'ملف'، 'صورة'، 'فيديو'، أو 'صوت'."))
            
            file_name = self.file.name.lower()
            if self.attachment_type == 'image' and self.file:
                if not (file_name.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'))):
                    raise ValidationError({'file': _("يجب أن يكون الملف صورة (png, jpg, jpeg, gif, bmp, tiff) إذا كان نوع المرفق 'صورة'.")})
            elif self.attachment_type == 'video' and self.file: # <--- تحقق من امتداد الفيديو
                if not (file_name.endswith(('.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'))):
                    raise ValidationError({'file': _("يجب أن يكون الملف فيديو (mp4, avi, mov, wmv, flv, webm) إذا كان نوع المرفق 'فيديو'.")})
            elif self.attachment_type == 'audio' and self.file: # <--- تحقق من امتداد الصوت
                if not (file_name.endswith(('.mp3', '.wav', '.ogg', '.aac', '.flac'))):
                    raise ValidationError({'file': _("يجب أن يكون الملف صوتًا (mp3, wav, ogg, aac, flac) إذا كان نوع المرفق 'صوت'.")})
        else:
            raise ValidationError({'attachment_type': _("نوع المرفق الأساسي غير صالح.")})
