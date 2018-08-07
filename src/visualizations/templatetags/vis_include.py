# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe

from action.evaluate import action_context_var, viz_number_context_var, tr_item
from action.models import Condition
from dataops import pandas_db
from visualizations.plotly import PlotlyColumnHistogram
from workflow.models import Column

register = template.Library()


def vis_html_content(context, column_name):
    # Get the action
    action = context.get(action_context_var, None)
    if not action:
        raise Exception('Action object not found when processing tag')
    workflow = action.workflow

    # Check if the column is correct
    if not Column.objects.filter(workflow=workflow, name=column_name).exists():
        raise Exception('Column {0} does not exist'.format(column_name))

    # Get the visualization number to generate unique IDs
    viz_number = context[viz_number_context_var]

    # Create the context for the visualization
    viz_ctx = {
        'style': 'width:400px; height:225px;',
        'id': 'viz_tag_{0}'.format(viz_number)
    }

    # If there is a column name in the context, insert it as individual value
    # If the template is simply being saved and rendered to detect syntax
    # errors, we may not have the data of an individual, so we have to relax
    # this restriction.
    ivalue = context.get(tr_item(column_name), None)
    if ivalue is not None:
        viz_ctx['individual_value'] = ivalue

    # Get the condition filter
    try:
        cond_filter = Condition.objects.get(action__id=action.id,
                                            is_filter=True)
    except ObjectDoesNotExist:
        cond_filter = None

    # Get the data from the data frame
    df = pandas_db.get_subframe(workflow.id,
                                cond_filter,
                                [column_name])
    # Get the visualisation
    viz = PlotlyColumnHistogram(data=df,
                                context=viz_ctx)

    prefix = ''
    if viz_number == 0:
        prefix = ''.join([
            '<script src="{0}"></script>'.format(x)
            for x in PlotlyColumnHistogram.get_engine_scripts()
        ])

    # Update viz number
    context[viz_number_context_var] = viz_number + 1

    # Return the rendering of the viz marked as safe
    return mark_safe(prefix + viz.render())


# Register the tag in the library.
register.simple_tag(func=vis_html_content,
                    takes_context=True,
                    name='visualization')
