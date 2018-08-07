# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from action.models import Action, Condition
from ontask.permissions import is_instructor
from .forms import (WorkflowImportForm,
                    WorkflowExportRequestForm)
from .models import Workflow
from .ops import (do_import_workflow,
                  do_export_workflow,
                  get_workflow)


@user_passes_test(is_instructor)
def export_ask(request, format=None):
    # Get the workflow
    workflow = get_workflow(request)
    if not workflow:
        return redirect('workflow:index')

    form = WorkflowExportRequestForm(request.POST or None,
                                     actions=workflow.actions.all(),
                                     put_labels=True)

    context = {
        'form': form,
        'name': workflow.name,
        'nrows': workflow.nrows,
        'ncols': workflow.ncols,
        'nactions': Action.objects.filter(workflow=workflow).count(),
        'wid': workflow.id
    }

    if request.method == 'POST':
        if form.is_valid():
            to_include = []
            for idx, a_id in enumerate(
                    Action.objects.filter(
                        workflow=workflow
                    ).values_list("id", flat=True)
            ):
                if form.cleaned_data['select_%s' % idx]:
                    to_include.append(str(a_id))
            return render(
                request,
                'workflow/export_done.html',
                {'include': ','.join(to_include),
                 'wid': workflow.id})

    # GET request, simply render the form
    return render(request, 'workflow/export.html', context)


@user_passes_test(is_instructor)
@require_http_methods(['GET'])
def export(request, data):
    """
    This request receives a parameter include with a comma separated list. The
    first value is a 0/1 stating if the data has to be included. The
    remaining elements are the ids of the actions to include
    :param request:
    :param data: Comma separated list of integers: First one is include: 0
    (do not include) or 1 include data and conditions, followed by the ids of
    the actions to include
    :return:
    """

    # Get the workflow
    workflow = get_workflow(request)
    if not workflow:
        return redirect('workflow:index')

    # Get the param encoding which elements to include in the export.
    action_ids = []
    if data and data != '':
        # Data has at least one integer
        try:
            action_ids = [int(x) for x in data.split(',')]
        except ValueError:
            return redirect('workflow:index')

    response = do_export_workflow(workflow, action_ids)

    return response


@user_passes_test(is_instructor)
def import_workflow(request):
    """
    View that handles a form for workflow import. It receives a file that
    needs to be unpacked and the data uploaded. In this method there are some
    basic checks to verify that the import procedure can go ahead.
    :param request: HTTP request
    :return: Rendering of the import page or back to the workflow index
    """
    form = WorkflowImportForm(request.POST or None, request.FILES or None)

    context = {'form': form}

    # If a get request or the form is not valid, render the page.
    if request.method == 'GET' or not form.is_valid():
        return render(request, 'workflow/import.html', context)


    new_wf_name = form.cleaned_data['name']
    if Workflow.objects.filter(user=request.user, name=new_wf_name).exists():
        # There is a workflow with this name. Return error.
        form.add_error(None, 'A workflow with this name already exists')
        return render(request, 'workflow/import.html', context)

    # Process the reception of the file
    if not form.is_multipart():
        form.add_error(None, 'Incorrect form request (it is not multipart)')
        return render(request, 'workflow/import.html', context)

    # UPLOAD THE FILE!
    status = do_import_workflow(request.user,
                                form.cleaned_data['name'],
                                request.FILES['file'])

    # If something went wrong, show at to the top of the page
    if status:
        messages.error(request, status)

    # Go back to the list of workflows
    return redirect('workflow:index')
