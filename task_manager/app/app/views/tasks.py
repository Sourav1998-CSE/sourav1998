import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from app.models import Team, Task, Comment
from app.forms import TaskCreationForm, TaskEditForm

@login_required
@require_http_methods(["GET", "POST"])
def task_create(request):
    """
    Any authenticated user is able to create task.
    """
    # Get request.user's teams
    teams = Team.objects.filter(leader=request.user)
    if request.method == 'POST':
        form = TaskCreationForm(request.POST, initial={'teams': teams})
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.creator = request.user
            new_task.save()
            # Task is firstly assigned to creator
            new_task.assigned_to.add(request.user)
            messages.success(request, "Task: `{0}` is created successfully!".format(new_task.title))
            # Task is created succesfully, redirect user to new task's detail page
            return redirect(new_task)
        else:
            # Form is not valid, send back with errors
            return render(
                request,
                'app/task_create-edit.html',
                {'user': request.user, 'form': form, 'creation': True}
            )
    else:
        form = TaskCreationForm(initial={'teams': teams})
        return render(
            request,
            'app/task_create-edit.html',
            {'user': request.user, 'form': form, 'teams': teams, 'creation': True}
        )

@login_required
@require_http_methods(["GET", "POST"])
def task_edit(request, task_id):
    """
    Only task creator is able to edit task.
    """
    task = get_object_or_404(Task, id=task_id)
    # Only task creator is allowed to edit task whose status is 'Planned'
    if request.user == task.creator and task.status == 'PLAN':
        teams = Team.objects.filter(leader=request.user)
        has_team = True if task.team else False
        members = task.team.members.all() if has_team else None
        if request.method == 'POST':
            form = TaskEditForm(
                request.POST,
                instance=task,
                initial={'members': members, 'has_team': has_team, 'teams': teams}
            )
            if form.is_valid():
                form.save()
                messages.success(request, "The changes are saved successfully!")
                return redirect(task)
            else:
                # Form is not valid, send back with errors
                return render(
                    request,
                    'app/task_create-edit.html',
                    {'user': request.user, 'form': form, 'task': task, 'creation': False}
                )
        else:
            form = TaskEditForm(
                instance=task,
                initial={'members': members, 'has_team': has_team, 'teams': teams}
            )
            return render(
                request,
                'app/task_create-edit.html',
                {'user': request.user, 'form': form, 'task': task, 'creation': False}
            )
    else:
        raise PermissionDenied

@login_required
@require_http_methods(["GET"])
def task_delete(request, task_id):
    """
    Only task creator can delete task if task is IN-PROGRESS.
    """
    task = get_object_or_404(Task, id=task_id)
    if request.user == task.creator and task.status == 'PLAN':
        task.delete()
        messages.success(request, "The task is deleted successfully!")
        # After deleting task redirect user to index page with success message
        return redirect('app:index')
    else:
        # User is not creator of task, raise PermissionDenied
        raise PermissionDenied

@login_required
@require_http_methods(["GET"])
def tasks(request):
    """
    Any authenticated user is able to see incomplete tasks
    created or assigned to him.
    """
    tasks = Task.objects.filter(
        Q(creator=request.user) | Q(assigned_to=request.user)
    ).exclude(status="COMP").distinct()
    return render(
        request,
        'app/tasks.html',
        {'user': request.user, 'tasks': tasks, 'completed': False}
    )

@login_required
@require_http_methods(["GET"])
def completed_tasks(request):
    """
    Any authenticated user is able to see completed tasks
    created or assigned to him.
    """
    tasks = Task.objects.filter(
        Q(creator=request.user) | Q(assigned_to=request.user)
    ).filter(status="COMP").distinct()
    return render(
        request,
        'app/tasks.html',
        {'user': request.user, 'tasks': tasks, 'completed': True}
    )

@login_required
@require_http_methods(["GET"])
def task_detail(request, task_id):
    """
    Only task creator and members of task's team can see details of task.
    """
    task = get_object_or_404(Task, id=task_id)
    if request.user == task.creator or request.user in task.assigned_to.all():
        allowed = True
    elif task.team:
        if request.user in task.team.members.all():
            allowed = True
        else:
            allowed = False
    else:
        allowed = False
    # If user is allowed to see details return details else raise PermissionDenied
    if allowed:
        return render(
            request,
            'app/task_detail.html',
            {'user': request.user, 'task': task}
            )
    else:
        raise PermissionDenied

@login_required
@require_http_methods(["GET"])
def task_accept(request, task_id):
    """
    Only assigned users can accept task and mark as In-Progress.
    """
    task = get_object_or_404(Task, id=task_id)
    if request.user in task.assigned_to.all():
        if task.status == 'PLAN':
            task.status = 'PROG'
            task.accepted_date = datetime.date.today()
            task.accepted_by = request.user
            task.save()
            messages.success(request, "The task has marked as In-Progress successfully!")
            # After marking task as In-Progress, redirect user to that task with success message
            return redirect(task)
        else:
            raise PermissionDenied
    else:
        raise PermissionDenied

@login_required
@require_http_methods(["GET"])
def task_mark_completed(request, task_id):
    """
    Only task creator and assigned users can mark task as Completed.
    """
    task = get_object_or_404(Task, id=task_id)
    if request.user == task.creator or request.user in task.assigned_to.all():
        if task.status == 'PROG':
            task.status = 'COMP'
            task.completed_date = datetime.date.today()
            task.save()
            messages.success(request, "The task is marked as Completed successfully!")
            # After marking task as completed, redirect user to that task with success message
            return redirect(task)
        else:
            raise PermissionDenied
    else:
        raise PermissionDenied

@login_required
@require_http_methods(["POST"])
def task_comment(request, task_id):
    """
    Only task creator, assigned users and members of task's team can comment on task.
    """
    task = get_object_or_404(Task, id=task_id)
    if request.user == task.creator or request.user in task.assigned_to.all():
        allowed = True
    elif task.team:
        if request.user in task.team.members.all():
            allowed = True
        else:
            allowed = False
    else:
        allowed = False
    # If user is allowed to comment, add comment else raise PermissionDenied
    if allowed:
        if request.POST.get('comment_body').strip():
            comment = Comment(
                author = request.user,
                task = task,
                body = request.POST['comment_body']
            )
            comment.save()
            messages.success(request, "The comment is added succesfully")
            # After adding the comment, redirect user to that task with success message
            return redirect(task)
        else:
            messages.error(request, "Missing required fields")
            return redirect(task)
    else:
        raise PermissionDenied
