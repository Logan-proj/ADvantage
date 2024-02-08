from django.http import HttpResponse
from django.template import loader

def login_view(request):
  template = loader.get_template('login.html')
  return HttpResponse(template.render())