from django.db import models
from accounts.models import AutoCreateAndAutoUpdateTimeStampedModel, User
from django.utils.translation import gettext_lazy as _
from teachers.models import Teacher
from subject.models import Subject

class SubjectContent(AutoCreateAndAutoUpdateTimeStampedModel):
    # الأنواع الأساسية للمحتوى الرئيسي
    CONTENT_TYPE_CHOICES = [
        ('text', _('نص')),
        ('link', _('رابط')),
        ('file', _('ملف رئيسي')), # لملف واحد أساسي (مثلاً PDF للمحاضرة)
    ]

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='contents',
        verbose_name=_("المادة الدراسية")
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
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        verbose_name=_("نوع المحتوى الأساسي"),
        help_text=_("اختر نوع المحتوى الأساسي: نص، رابط، أو ملف رئيسي.")
    )

    # الحقول الأساسية للمحتوى
    text_content = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("المحتوى النصي"),
        help_text=_("اكتب المحتوى النصي إذا كان نوع المحتوى الأساسي 'نص'.")
    )
    link_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("رابط URL"),
        help_text=_("أدخل رابط URL إذا كان نوع المحتوى الأساسي 'رابط'.")
    )
    main_file = models.FileField( # لرفع ملف أساسي واحد
        upload_to='subject_content_main_files/',
        blank=True,
        null=True,
        verbose_name=_("الملف الرئيسي"),
        help_text=_("رفع ملف رئيسي (مثل PDF) إذا كان نوع المحتوى الأساسي 'ملف'.")
    )

    # **الحقول الجديدة للصور والمستندات الإضافية**
    # ستضيف هنا عددًا محددًا من الحقول للصور الإضافية أو المستندات،
    # لأنك لا تريد نموذجًا منفصلاً لـ Many-to-Many.
    # هذا يعني أنك تحدد أقصى عدد من الصور يمكن ربطها بكل محتوى.
    image1 = models.ImageField(
        upload_to='subject_content_images/',
        blank=True,
        null=True,
        verbose_name=_("صورة إضافية 1")
    )
    image2 = models.ImageField(
        upload_to='subject_content_images/',
        blank=True,
        null=True,
        verbose_name=_("صورة إضافية 2")
    )
    image3 = models.ImageField(
        upload_to='subject_content_images/',
        blank=True,
        null=True,
        verbose_name=_("صورة إضافية 3")
    )
    # يمكنك الاستمرار في إضافة image4, image5... إلخ حسب حاجتك.

    document1 = models.FileField(
        upload_to='subject_content_documents/',
        blank=True,
        null=True,
        verbose_name=_("مستند إضافي 1")
    )
    # يمكنك الاستمرار في إضافة document2, document3... إلخ

    class Meta:
        verbose_name = _("محتوى المادة")
        verbose_name_plural = _("محتويات المواد")
        ordering = ['subject', 'title']

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()}) - {self.subject.name}"

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError

        # التحقق من أن حقل المحتوى الأساسي الصحيح فقط ممتلئ
        if self.content_type == 'text':
            if not self.text_content:
                raise ValidationError({'text_content': _("يجب إدخال محتوى نصي إذا كان نوع المحتوى 'نص'.")})
            if self.link_url or self.main_file:
                raise ValidationError(_("لا يمكن أن يحتوي المحتوى على رابط أو ملف إذا كان نوعه 'نص'."))
        elif self.content_type == 'link':
            if not self.link_url:
                raise ValidationError({'link_url': _("يجب إدخال رابط URL إذا كان نوع المحتوى 'رابط'.")})
            if self.text_content or self.main_file:
                raise ValidationError(_("لا يمكن أن يحتوي المحتوى على نص أو ملف إذا كان نوعه 'رابط'."))
        elif self.content_type == 'file':
            if not self.main_file:
                raise ValidationError({'main_file': _("يجب رفع ملف إذا كان نوع المحتوى 'ملف'.")})
            if self.text_content or self.link_url:
                raise ValidationError(_("لا يمكن أن يحتوي المحتوى على نص أو رابط إذا كان نوعه 'ملف'."))
        else:
            raise ValidationError({'content_type': _("نوع المحتوى الأساسي غير صالح.")})

        # ملاحظة: هذا المنطق لا يمنعك من رفع ملف رئيسي (main_file)
        # ورفع صور إضافية (image1, image2) في نفس السجل،
        # وهذا يتوافق مع متطلبك "فايل وعدة صور لنفس العنوان".
        # لا توجد قيود إضافية هنا على حقول imageX أو documentX
        # لأنها مسموحة دائماً بغض النظر عن content_type الأساسي.