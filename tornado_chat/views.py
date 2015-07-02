from django.shortcuts import render_to_response
from tornado_chat.forms import LoginForm, RegForm
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth


@csrf_exempt
def log_in_chat(request):
    log_form = LoginForm()


    if request.method=='POST' and ('log_form' in request.POST):
        log_form=LoginForm(request.POST)


        if log_form.is_valid():
            user = log_form.log_in(request)


            if user is not None:
                return HttpResponseRedirect(reverse('privatemessages.views.messages_view'))


    return render_to_response('log_in_page.html',{"log_form":log_form})


@csrf_exempt
def reg(request):
    reg_form=RegForm()
    if request.method=='POST' and ('reg_form' in request.POST):
        reg_form=RegForm(request.POST)
        if reg_form.is_valid():
            reg_form.create_user()
            user=auth.authenticate(username=request.POST.get("username"),password=request.POST.get("password"))
            auth.login(request, user)

            return HttpResponseRedirect(reverse('privatemessages.views.messages_view'))
    return render_to_response('registration.html',{'reg_form':reg_form})


