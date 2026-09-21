from django.http import JsonResponse
from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def about(request):
    return render(request, "core/about.html")


def help_center(request):
    return render(request, "core/help.html")


def terms(request):
    return render(request, "core/terms.html")


def health(request):
    return JsonResponse({"status": "ok", "service": "vaulta-web"})
