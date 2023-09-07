from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from app.models import Team

@require_http_methods(["GET"])
def index(request):
    if request.user.is_authenticated:
        teams = request.user.team_set.all()
        return render(
            request,
            'app/index.html',
            {'user' : request.user, 'teams' : teams}
        )
    else:
        return render(request, 'app/index.html', {'user' : request.user})
