from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone

from .models import Todo, Notification


@login_required
def todo_list(request):
    status = request.GET.get('status', '')
    todos = Todo.objects.filter(assignee=request.user)
    if status:
        todos = todos.filter(status=status)
    return render(request, 'todos/todo_list.html', {'todos': todos})


@login_required
def todo_create(request):
    if request.method == 'POST':
        Todo.objects.create(
            title=request.POST.get('title'),
            content=request.POST.get('content'),
            todo_type=request.POST.get('todo_type', 'personal'),
            priority=request.POST.get('priority', 'normal'),
            due_date=request.POST.get('due_date') or None,
            assignee=request.user,
            creator=request.user,
        )
        messages.success(request, '待办创建成功')
        return redirect('todo_list')
    return render(request, 'todos/todo_form.html')


@login_required
def todo_edit(request, pk):
    todo = get_object_or_404(Todo, pk=pk, assignee=request.user)
    
    if request.method == 'POST':
        todo.title = request.POST.get('title')
        todo.content = request.POST.get('content')
        todo.todo_type = request.POST.get('todo_type', 'personal')
        todo.priority = request.POST.get('priority', 'normal')
        todo.due_date = request.POST.get('due_date') or None
        todo.save()
        messages.success(request, '待办更新成功')
        return redirect('todo_list')
    
    return render(request, 'todos/todo_form.html', {'todo': todo})


@login_required
def todo_complete(request, pk):
    if request.method == 'POST':
        todo = get_object_or_404(Todo, pk=pk, assignee=request.user)
        todo.status = 'completed'
        todo.completed_at = timezone.now()
        todo.save()
        messages.success(request, '待办已完成')
    return redirect('todo_list')


@login_required
def todo_delete(request, pk):
    if request.method == 'POST':
        todo = get_object_or_404(Todo, pk=pk, assignee=request.user)
        todo.delete()
        messages.success(request, '待办删除成功')
    return redirect('todo_list')


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    return render(request, 'todos/notification_list.html', {'notifications': notifications})


@login_required
def notification_read(request, pk):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
    return redirect('notification_list')


@login_required
def notification_mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True, read_at=timezone.now())
    messages.success(request, '所有通知已标记为已读')
    return redirect('notification_list')


@login_required
def api_notification_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})
