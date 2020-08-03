# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from pypro.modulos import facade


def indice(request):
    ctx = {
        'modulos': facade.listar_modulos_com_aulas()
    }
    return render(request, 'modulos/indice.html', ctx)


def detalhe(request, slug):
    modulo = facade.encontrar_modulo(slug)
    aulas = facade.lista_aula_de_modulo_ordenadas(modulo)
    return render(request, 'modulos/modulo_detalhe.html', {'modulo': modulo, 'aulas': aulas})


@login_required()
def aula(request, slug):
    n = facade.econtrar_aula(slug)
    return render(request, 'modulos/aula_detalhe.html', {'aula': n})
