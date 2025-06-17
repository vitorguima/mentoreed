from django.shortcuts import render

def anvisa_view(request):
    return render(request, "anvisa.html")