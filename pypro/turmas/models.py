from django.contrib.auth import get_user_model
from django.db import models


# Create your models here.

class Turma(models.Model):
    nome = models.CharField(max_length=64)
    slug = models.SlugField(max_length=64)
    inicio = models.DateField()
    fim = models.DateField()
    alunos = models.ManyToManyField(get_user_model(), through='Matricula')


class Matricula(models.Model):
    usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    turma = models.ForeignKey('Turma', on_delete=models.CASCADE)
    data = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = [['usuario', 'turma']]
        ordering = ['turma', 'data']
