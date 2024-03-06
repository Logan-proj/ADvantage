#from django.http import HttpResponse
#from django.template import loader

#def login_view(request):
#  template = loader.get_template('login.html')
#  return HttpResponse(template.render())

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect to a success page.
            return redirect('dashboard')  # Change 'home' to your desired route
        else:
            # Return an 'invalid login' error message.
            messages.error(request, 'Invalid username or password.')
            
    return render(request, 'login.html')
