



import redis

# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from django.http import  HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt



from django.contrib.auth.models import User

from privatemessages.models import Thread

from privatemessages.utils import json_response, send_message






#Send message through Django, use only for first message
def send_message_view(request):
    if not request.method=='POST':
        return HttpResponse('Please use POST method')

    if not request.user.is_authenticated():
        return HttpResponse('Please sign in')

    message_text=request.POST.get('message')

    if not message_text:
        return HttpResponse("You can't send empty message ")

    if len(message_text)>1000:
        return  HttpResponse('The message must be less than 1000 characters')

    recipient_name= request.POST.get('recipient_name')

    try:
        recipient=User.objects.get(username=recipient_name)
    except User.DoesNotExist:
        return HttpResponse("This user does not exist.")

    if recipient == request.user:
        return HttpResponse("You can't send message to yourself")

    thread_queryset=Thread.objects.filter(
        participants=recipient
    ).filter(
        participants=request.user
    )


    if thread_queryset.exists():
        thread = None
        for current_thread in thread_queryset:
            if current_thread.participants.count() == 2:
                thread = current_thread
                break
    if not thread_queryset.exists() or thread == None :
        thread=Thread.objects.create()
        thread.participants.add(request.user, recipient)

    send_message(
        thread.id,
        request.user.id,
        message_text,
        request.user.username,
    )

    return HttpResponseRedirect(
        reverse('privatemessages.views.messages_view')
    )



#Send message through Tornado
@csrf_exempt
def send_message_api_view(request,thread_id):
    print ("message")
    if not request.method=='POST':
        return json_response({"error":"Please use POST"})

    try:
        thread = Thread.objects.get(id = thread_id)
    except Thread.DoesNotExist:
        return json_response({"error":"No such thread"})

    try:
        sender=User.objects.get(id=request.POST.get("sender_id"))
    except User.DoesNotExist:
        return json_response({"error":"No such user."})

    message_text=request.POST.get("message")

    if not message_text:
        return json_response({"error":"Message text cannot be empty"})

    if len(message_text)>1000:
        return json_response({"error":"The message must be less than 1000 characters."})

    send_message(
        thread.id,
        sender.id,
        message_text
    )

    return json_response({"status":"Ok"})


#View recipients
def messages_view(request):
    if not request.user.is_authenticated():
        return HttpResponse("Please log in")

    threads=Thread.objects.filter(
        participants=request.user
    ).order_by("-last_message")

    if not threads:
        return render_to_response("private_messages.html",{},context_instance=RequestContext(request))

    r=redis.StrictRedis()

    user_id=str(request.user.id)

    for thread in threads:
        #thread.partner= thread.participants.exclude(id=request.user.id)[0]
        thread.partners= thread.participants.exclude(id=request.user.id)


        thread.total_messages=r.hget(
            "".join(["thread_",str(thread.id),"_messages"]),
            "total_messages"
        )

    return render_to_response('private_messages.html',
                              {
                                  "threads":threads,
                              }, context_instance=RequestContext(request)
                              )


 #View of chat messages
def chat_view(request, thread_id):
    if not request.user.is_authenticated():
        return HttpResponse("Please log in")

    thread = get_object_or_404(
        Thread,
        id=thread_id,
        participants__id=request.user.id
    )

    messages=thread.message_set.order_by("-datetime")[:100]

    user_id=str(request.user.id)

    r=redis.StrictRedis()

    messages_total=r.hget(
        "".join(["thread_",thread_id,"_messages"]),
        "total_messages"
    )

    messages_sent=r.hget(
        "".join(["thread_",thread_id,"_messages"]),
        "".join(["from_",user_id])
    )

    if messages_total:
        messages_total=int(messages_total)
    else:
        messages_total=0

    if messages_sent:
        messages_sent=int(messages_sent)
    else:
        messages_sent=0

    messages_received=messages_total-messages_sent


    partners=thread.participants.exclude(id=request.user.id)


    tz=request.COOKIES.get("timezone")

    if tz:
        timezone.activate(tz)

    return render_to_response('chat.html',
                              {
                                  "thread_id":thread_id,
                                  "thread_messages":messages,
                                  "messages_total":messages_total,
                                  "messages_sent":messages_sent,
                                  "messages_received":messages_received,
                                  "partners":partners,
                              },
                              context_instance=RequestContext(request))


@csrf_exempt
def edit_user_set(request, thread_id):
     #Function get an inforamtion from tornado app about
     # delete or add some user and username of target,
     # it also get thread_id

     print("Request get")
     if not request.method == "POST":
         json_response({"error":"Please use POST method"})

     try:
          thread = Thread.objects.get(id = thread_id)
     except Thread.DoesNotExist:
         json_response({"error":"This thread does not exist"})


     username = request.POST.get("username")
     try:
         target_user = User.objects.get(username = username)
     except User.DoesNotExist:
         json_response("This user does not exist")

     if request.POST.get("operation") == "add_user":

         print ("b3_!")
         try:
             thread.participants.get (username = username)
             print ("User not added")
         except User.DoesNotExist:
             thread.participants.add(target_user)
             print ("User added")
             return json_response({"status":"Ok"})

     return json_response({"error":"This user is already in thread"})





