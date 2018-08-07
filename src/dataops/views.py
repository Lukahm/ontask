# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from datetime import datetime

import django_tables2 as tables
import pandas as pd
import pytz
from django.conf import settings as ontask_settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import redirect, render, reverse
from django.template.loader import render_to_string
from django.views.decorators.cache import cache_page

import dataops.ops as ops
import logs.ops
from dataops import pandas_db
from dataops.forms import SelectColumnForm
from dataops.plugin_manager import run_plugin
from ontask.permissions import is_instructor
from ontask.tables import OperationsColumn
from workflow.ops import get_workflow
from .forms import RowForm, field_prefix
from .models import PluginRegistry
from .plugin_manager import refresh_plugin_data, load_plugin


class PluginRegistryTable(tables.Table):
    """
    Table to render the list of plugins available for execution. The
    Operations column is inheriting from another class to centralise the
    customisation.
    """

    filename = tables.Column(verbose_name=str('Folder'))

    name = tables.Column(verbose_name=str('Name'))

    description_txt = tables.Column(verbose_name=str('Description'))

    modified = tables.DateTimeColumn(verbose_name='Last modified')

    executed = tables.DateTimeColumn(verbose_name='Last executed')

    operations = OperationsColumn(
        verbose_name='Operations',
        template_file='dataops/includes/partial_plugin_operations.html',
        template_context=lambda record: {'id': record.id,
                                         'is_verified': record.is_verified}
    )

    class Meta:
        model = PluginRegistry

        fields = ('filename', 'name', 'description_txt', 'modified',
                  'is_verified', 'executed')

        sequence = ('filename', 'name', 'description_txt', 'modified',
                    'is_verified', 'executed')

        attrs = {
            'class': 'table display table-bordered',
            'id': 'transform-table'
        }

        row_attrs = {
            'style': 'text-align:center;',
        }


@cache_page(60 * 15)
@user_passes_test(is_instructor)
def uploadmerge(request):
    return render(request, 'dataops/uploadmerge.html', {})


@user_passes_test(is_instructor)
def transform(request):
    # Get the workflow that is being used
    workflow = get_workflow(request)
    if not workflow:
        return redirect('workflow:index')

    # Traverse the plugin folder and refresh the db content.
    refresh_plugin_data(request, workflow)

    table = PluginRegistryTable(PluginRegistry.objects.all(),
                                orderable=False)

    return render(request, 'dataops/transform.html', {'table': table})


@user_passes_test(is_instructor)
def diagnose(request, pk):
    """
    HTML request to show the diagnostics of a plugin that failed the
    verification tests.

    :param request: HTML request object
    :param pk: Primary key of the transform element
    :return:
    """

    # To include in the JSON response
    data = dict()

    # Action being used
    try:
        plugin = PluginRegistry.objects.get(id=pk)
    except ObjectDoesNotExist:
        data['form_is_valid'] = True
        data['html_redirect'] = reverse('dataops:transform')
        return JsonResponse(data)

    # Reload the plugin to get the messages stored in the right place.
    pinstance, msgs = load_plugin(plugin.filename)

    # If the new instance is now properly verified, simply redirect to the
    # transform page
    if pinstance:
        plugin.is_verified = True
        plugin.save()
        data['form_is_valid'] = True
        data['html_redirect'] = reverse('dataops:transform')

        return JsonResponse(data)

    # Get the diagnostics from the plugin and use it for rendering.
    data['html_form'] = render_to_string(
        'dataops/includes/partial_diagnostics.html',
        {'diagnostic_table': msgs},
        request=request)
    return JsonResponse(data)


@user_passes_test(is_instructor)
def row_update(request):
    """
    Receives a POST request to update a row in the data table
    :param request: Request object with all the data.
    :return:
    """

    # If there is no workflow object, go back to the index
    workflow = get_workflow(request)
    if not workflow:
        return redirect('workflow:index')

    # If the workflow has no data, something went wrong, go back to the
    # main dataops page
    if workflow.nrows == 0:
        return redirect('dataops:uploadmerge')

    # Get the pair key,value to fetch the row from the table
    update_key = request.GET.get('update_key', None)
    update_val = request.GET.get('update_val', None)

    if not update_key or not update_val:
        # Malformed request
        return render(request, 'error.html',
                      {'message': 'Unable to update table row'})

    # Get the rows from the table
    rows = pandas_db.execute_select_on_table(workflow.id,
                                             [update_key],
                                             [update_val])

    row_form = RowForm(request.POST or None,
                       workflow=workflow,
                       initial_values=list(rows[0]))

    if request.method == 'GET' or not row_form.is_valid():
        return render(request,
                      'dataops/row_filter.html',
                      {'workflow': workflow,
                       'row_form': row_form,
                       'cancel_url': reverse('table:display')})

    # This is a valid POST request

    # Create the query to update the row
    set_fields = []
    set_values = []
    columns = workflow.get_columns()
    unique_names = [c.name for c in columns if c.is_key]
    unique_field = None
    unique_value = None
    log_payload = []
    for idx, col in enumerate(columns):
        value = row_form.cleaned_data[field_prefix + '%s' % idx]
        set_fields.append(col.name)
        set_values.append(value)
        log_payload.append((col.name, str(value)))

        if not unique_field and col.name in unique_names:
            unique_field = col.name
            unique_value = value

    # If there is no unique key, something went wrong.
    if not unique_field:
        raise Exception('Key value not found when updating row')

    pandas_db.update_row(workflow.id,
                         set_fields,
                         set_values,
                         [unique_field],
                         [unique_value])

    # Recompute all the values of the conditions in each of the actions
    for act in workflow.actions.all():
        act.update_n_rows_selected()

    # Log the event
    logs.ops.put(request.user,
                 'tablerow_update',
                 workflow,
                 {'id': workflow.id,
                  'name': workflow.name,
                  'new_values': log_payload})

    return redirect('table:display')


@user_passes_test(is_instructor)
def row_create(request):
    """
    Receives a POST request to create a new row in the data table
    :param request: Request object with all the data.
    :return:
    """

    # If there is no workflow object, go back to the index
    workflow = get_workflow(request)
    if not workflow:
        return redirect('workflow:index')

    # If the workflow has no data, the operation should not be allowed
    if workflow.nrows == 0:
        return redirect('dataops:uploadmerge')

    # Create the form
    form = RowForm(request.POST or None, workflow=workflow)

    if request.method == 'GET' or not form.is_valid():
        return render(request,
                      'dataops/row_create.html',
                      {'workflow': workflow,
                       'form': form,
                       'cancel_url': reverse('table:display')})

    # Create the query to update the row
    columns = workflow.get_columns()
    column_names = [c.name for c in columns]
    field_name = field_prefix + '%s'
    row_vals = [form.cleaned_data[field_name % idx]
                for idx in range(len(columns))]

    # Load the existing df from the db
    df = pandas_db.load_from_db(workflow.id)

    # Perform the row addition in the DF first
    # df2 = pd.DataFrame([[5, 6], [7, 8]], columns=list('AB'))
    # df.append(df2, ignore_index=True)
    new_row = pd.DataFrame([row_vals], columns=column_names)
    df = df.append(new_row, ignore_index=True)

    # Verify that the unique columns remain unique
    for ucol in [c for c in columns if c.is_key]:
        if not ops.is_unique_column(df[ucol.name]):
            form.add_error(
                None,
                'Repeated value in column ' + ucol.name + '.' +
                ' It must be different to maintain Key property'
            )
            return render(request,
                          'dataops/row_create.html',
                          {'workflow': workflow,
                           'form': form,
                           'cancel_url': reverse('table:display')})

    # Restore the dataframe to the DB
    ops.store_dataframe_in_db(df, workflow.id)

    # Recompute all the values of the conditions in each of the actions
    for act in workflow.actions.all():
        act.update_n_rows_selected()

    # Log the event
    log_payload = zip(column_names, [str(x) for x in row_vals])
    logs.ops.put(request.user,
                 'tablerow_create',
                 workflow,
                 {'id': workflow.id,
                  'name': workflow.name,
                  'new_values': log_payload})

    # Done. Back to the table view
    return redirect('table:display')


@user_passes_test(is_instructor)
def run(request, pk):
    """
    View provided as the first step to execute a plugin.
    :param request: HTTP request received
    :param pk: primary key of the plugin
    :return: Page offering to select the columns to invoke
    """

    # Get the workflow and the plugin information
    workflow = get_workflow(request)
    if not workflow:
        return redirect('workflow:index')
    try:
        plugin_info = PluginRegistry.objects.get(pk=pk)
    except PluginRegistry.DoesNotExist:
        return redirect('workflow:index')

    plugin_instance, msgs = load_plugin(plugin_info.filename)
    if plugin_instance is None:
        messages.error(
            request,
            'Unable to instantiate plugin "{0}"'.format(plugin_info.name)
        )
        return redirect('dataops:transform')

    if len(plugin_instance.input_column_names) > 0:
        # The plug in works with a fixed set of columns
        cnames = workflow.columns.all().values_list('name', flat=True)
        if not set(plugin_instance.input_column_names) < set(cnames):
            # The set of columns are not part of the workflow
            messages.error(
                request,
                'Workflow does not have the correct columns to run this plugin'
            )
            return redirect('dataops:transform')

    # create the form to select the columns and the corresponding dictionary
    form = SelectColumnForm(request.POST or None,
                            workflow=workflow,
                            plugin_instance=plugin_instance)

    # Set the basic elements in the context
    context = {
        'form': form,
        'output_column_fields': [x for x in list(form)
                                 if x.name.startswith(field_prefix + 'output')],
        'parameters': [x for x in list(form)
                       if x.name.startswith(field_prefix + 'parameter')],
        'pinstance': plugin_instance,
        'id': workflow.id
    }

    # If it is a GET request or non valid, render the form.
    if request.method == 'GET' or not form.is_valid():
        return render(request,
                      'dataops/plugin_info_for_run.html',
                      context)

    # POST is correct proceed with execution

    # Get the data frame and select the appropriate columns
    try:
        dst_df = pandas_db.load_from_db(workflow.id)
    except Exception:
        messages.error(request, 'Exception while retrieving the data frame')
        return render(request, 'error.html', {})

    # Take the list of inputs from the form if empty list is given.
    if not plugin_instance.input_column_names:
        plugin_instance.input_column_names = \
            [c.name for c in form.cleaned_data['columns']]

    # Get the proper subset of the data frame
    sub_df = dst_df[[form.cleaned_data['merge_key']] +
                    plugin_instance.input_column_names]

    # Process the output columns
    for idx, output_cname in enumerate(plugin_instance.output_column_names):
        new_cname = form.cleaned_data[field_prefix + 'output_%s' % idx]
        if form.cleaned_data['out_column_suffix']:
            new_cname += form.cleaned_data['out_column_suffix']
        plugin_instance.output_column_names[idx] = new_cname

    # Pack the parameters
    params = dict()
    for idx, tpl in enumerate(plugin_instance.parameters):
        params[tpl[0]] = form.cleaned_data[field_prefix + 'parameter_%s' % idx]

    # Execute the plugin
    result_df, status = run_plugin(plugin_instance,
                                   sub_df,
                                   form.cleaned_data['merge_key'],
                                   params)

    if status is not None:
        context['exec_status'] = status

        # Log the event
        logs.ops.put(request.user,
                     'plugin_execute',
                     workflow,
                     {'id': plugin_info.id,
                      'name': plugin_info.name,
                      'status': status})

        return render(request,
                      'dataops/plugin_execution_report.html',
                      context)

    # Additional checks
    # Result has the same number of rows
    if result_df.shape[0] != dst_df.shape[0]:
        status = 'Incorrect number of rows in result data frame.'
        context['exec_status'] = status

        # Log the event
        logs.ops.put(request.user,
                     'plugin_execute',
                     workflow,
                     {'id': plugin_info.id,
                      'name': plugin_info.name,
                      'status': status})

        return render(request,
                      'dataops/plugin_execution_report.html',
                      context)

    # Result column names are consistent
    if set(result_df.columns) != \
            set([form.cleaned_data['merge_key']] +
                plugin_instance.output_column_names):
        status = 'Incorrect columns in result data frame.'
        context['exec_status'] = status

        # Log the event
        logs.ops.put(request.user,
                     'plugin_execute',
                     workflow,
                     {'id': plugin_info.id,
                      'name': plugin_info.name,
                      'status': status})

        return render(request,
                      'dataops/plugin_execution_report.html',
                      context)

    # Proceed with the merge
    try:
        result = ops.perform_dataframe_upload_merge(
            workflow.id,
            dst_df,
            result_df,
            {'how_merge': 'left',
             'dst_selected_key': form.cleaned_data['merge_key'],
             'src_selected_key': form.cleaned_data['merge_key'],
             'initial_column_names': list(result_df.columns),
             'rename_column_names': list(result_df.columns),
             'columns_to_upload': [True] * len(list(result_df.columns))}
        )
    except Exception as e:
        context['exec_status'] = e.message
        return render(request,
                      'dataops/plugin_execution_report.html',
                      context)

    if isinstance(result, str):
        # Something went wrong
        context['exec_status'] = result
        return render(request,
                      'dataops/plugin_execution_report.html',
                      context)

    # Get the resulting dataframe
    final_df = pandas_db.load_from_db(workflow.id)

    # Update execution time
    plugin_info.executed = datetime.now(
        pytz.timezone(ontask_settings.TIME_ZONE)
    )
    plugin_info.save()

    # List of pairs (column name, column type) in the result to create the
    # log event
    result_columns = zip(
        list(result_df.columns),
        pandas_db.df_column_types_rename(result_df))

    # Log the event
    logs.ops.put(request.user,
                 'plugin_execute',
                 workflow,
                 {'id': plugin_info.id,
                  'name': plugin_info.name,
                  'status': status,
                  'result_columns': result_columns})

    # Create the table information to show in the report.
    column_info = []
    dst_names = list(dst_df.columns)
    result_names = list(result_df.columns)
    for c in list(final_df.columns):
        if c not in result_names:
            column_info.append((c, ''))
        elif c not in dst_names:
            column_info.append(('', c + ' (New)'))
        else:
            if c == form.cleaned_data['merge_key']:
                column_info.append((c, c))
            else:
                column_info.append((c + ' (Update)', c))

    context['info'] = column_info
    context['key'] = form.cleaned_data['merge_key']
    context['id'] = workflow.id

    # Redirect to the notification page with the proper info
    return render(request,
                  'dataops/plugin_execution_report.html',
                  context)
