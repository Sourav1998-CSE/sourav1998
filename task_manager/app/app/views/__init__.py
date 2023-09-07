from app.views.auth import login, signup, logout
from app.views.teams import (
    team_create, team_detail, team_add_member, team_remove_member, team_delete
)
from app.views.index import index
from app.views.tasks import (
    task_create, tasks, completed_tasks, task_detail, task_edit,
    task_accept, task_mark_completed, task_comment, task_delete
)
from app.views.search import task_search
