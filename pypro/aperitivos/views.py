from django.shortcuts import render


# Create your views here.


def video(request, slug):
    videos = {
        'motivacao': {
            'titulo': 'Video Aperitivo: Motivação',
            'vimeo_id': 440789232
        },
        'instalacao-windows': {
            'titulo': 'Instalacao Windows',
            'vimeo_id': 251497668
        },
    }
    video = videos[slug]
    return render(request, 'aperitivos/video.html', context={'video': video})
