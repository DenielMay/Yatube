from django import forms

from django.core.exceptions import ValidationError

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == "":
            raise ValidationError('Введите текс записи')
        return data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {'text': 'Введите текст комментария к посту'}