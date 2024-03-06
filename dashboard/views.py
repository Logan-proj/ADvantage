from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    template = loader.get_template('dashboard.html')
    return HttpResponse(template.render())