from django.http import HttpResponse
from django.template import loader
from .models import Message


def index(request):
    template = loader.get_template("index.html")
    messages = Message.objects.all().order_by("created_at")
    context = {
        "messages": messages,
    }
    return HttpResponse(template.render(context, request))
