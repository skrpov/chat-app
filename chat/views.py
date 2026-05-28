from django.http import HttpResponse
from django.template import loader
from .models import Message
from django.contrib.auth.decorators import login_required


@login_required
def messenger_view(request):
    template = loader.get_template("messenger.html")
    messages = Message.objects.all().order_by("created_at")
    context = {
        "messages": messages,
        "display_name": request.user.username,
    }
    return HttpResponse(template.render(context, request))
