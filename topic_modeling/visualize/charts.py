# The Topical Guide
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topical Guide is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topical Guide is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topical Guide, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

# General python from imports
from collections import defaultdict
from django import forms
from django.forms.widgets import Input
from numpy import arange, zeros
from scipy import linspace, stats
from scipy.stats.kde import gaussian_kde
from topic_modeling.visualize.models import Analysis, Attribute, AttributeValue, \
    AttributeValueTopic, Dataset, Topic, TopicMetric, Value
import StringIO
import math
import csv

import matplotlib
#Avoid using X windows by setting a backend that doesn't use it. This is necessary for headless setups
#matplotlib.use("Cairo")
import pylab

# General python imports

# Django imports

# Local (topic_modeling) imports

# Some auxiliary variables
##########################
plotting_colors = [ "red", "green", "blue", "pink", "orange", "slategray",
                "lightsalmon", "ghostwhite", "linen", "coral", "dodgerblue",
                "aliceblue", "darkseagreen", "tomato", "limegreen",
                "peachpuff", "navy", "crimson", "lightpink", "yellow",
                "bisque", "silver", "blueviolet", "blueviolet", "honedew",
                "steelblue", "olivedrab", "green", "burlywood", "lightcyan",
                "gray", "tan", "firebrick", "royalblue", "orange",
                "lightyellow", "teal", "florawhite", "cyan", "mediumblue",
                "forestgreen", "mediumvioletred", "palegreen", "darkgreen",
                "azure", "darkorange", "beige", "mediumturquoise",
                "lightskyblue", "dimgray", "salmon", "mediumpurple",
                "mediumseagreen", "khaki", "darkgray", "darkslategray", "snow",
                "lightseagreen", "darkviolet", "indianred", "lemonchiffon",
                "palevioletred", "slateblue", "midnightblue", "pink", "orchid",
                "darkblue", "whitesmoke", "black", "springgreen", "lightcoral",
                "lightslategray", "wheat", "powderblue", "lightgreen",
                "mediumaquamarine", "maroon", "chartreuse", "ivory", "plum",
                "mistyrose", "brown", "greenyellow", "turquoise",
                "mediumslateblue", "darkorchid", "purple", "mintcream", "peru",
                "orangered", "darkslateblue", "hotpink", "darkcyan",
                "goldenrod", "skyblue", "navajowhite", "sandybrown",
                "lightgoldenrodyellow", "lightgrey", "lightsteelblue",
                "darkgoldenrod", "aqua", "chocolate", "indigo", "moccasin",
                "gold", "yellowgreen", "aquamarine", "lightblue", "white"]

# Helper methods
################

def get_chart(words):
    if len(words) == 0:
        return ""

    url = "http://chart.apis.google.com/chart?cht=bhs&chs=200x300&chxt=x,y"
    data = "&chd=t:"
    axislabel = ""

    for word in words[:10]:
        data += "%f," % word.percent
        axislabel = "|" + word.word + axislabel
    axislabel = "&chxl=1:" + axislabel

    max_ = math.ceil(float(words[0].percent))

    size = "&chds=0.0,%s" % max_
    xsize = "&chxr=0,0,%s,1.0" % max_

    data = data[:-1]
    return url + data + axislabel + size + xsize


def thin_labels(labels, interval):
    """ Reduce the number of labels for a plot axis when there are too many.

    This is accomplished by "thinning" the labels, selecting every interval-th
    one and discarding all others.
    Args:
        labels: List<labels>, the list of labels to be thinned.
        interval: int, the interval at which labels will be selected for the
            thinned list
    Returns:
        A thinned version of the list.
    """

    thinned_labels = []
    for i in range(len(labels)):
        if i % interval == 0:
            thinned_labels.append(labels[i])
        else:
            thinned_labels.append("")
    return thinned_labels


# Classes used by the plots tab
###############################

class Chart(object):
    def __init__(self, chart_parameters):
        """
        Args:
            chart_parameters: is a dictionary that maps parameter names to their
                values, probably as strings
        """
        self.chart_parameters = chart_parameters

    def get_chart_image(self):
        raise NotImplementedError("Abstract chart class.  Does not implement"
                                  "get_chart_image")


# Topics vs. Attributes Classes
##################################

class Button(Input):
    input_type = 'button'

    def __init__(self, attrs=None, value=None, onClick=None):
        super(Button, self).__init__(attrs)
        if value:
            self.attrs['value'] = value
        if onClick:
            self.attrs['onClick'] = onClick

class TopicAttributePlotForm(forms.Form):

    def __init__(self, dataset, analysis, *args, **kwargs):
        super(TopicAttributePlotForm, self).__init__(*args, **kwargs)

        #The list of topics
        topics = analysis.topic_set.all()
        self.fields['topics'] = forms.ModelMultipleChoiceField(topics,
                initial=topics[0:3])
        self.fields['topics'].widget.attrs['onchange'] = \
                'update_topic_attribute_plot()'
        self.fields['topics'].widget.attrs['class'] = 'under-label'

        #Available attributes
        attributes = dataset.attribute_set.all()
        self.fields['attribute'] = forms.ModelChoiceField(attributes,
                initial=attributes[0], widget=forms.Select())
        self.fields['attribute'].widget.attrs['onchange'] = \
                'update_attribute_values()'
        self.fields['attribute'].widget.attrs['class'] = 'under-label'

        #Frequency checkbox
        self.fields['by_frequency'] = forms.BooleanField(required=False)
        self.fields['by_frequency'].widget.attrs['onchange'] = \
                'update_topic_attribute_plot()'
        self.fields['by_frequency'].widget.attrs['class'] = 'beside-label'

        #Histogram checkbox
        self.fields['histogram'] = forms.BooleanField(required=False)
        self.fields['histogram'].widget.attrs['onchange'] = \
                'update_topic_attribute_plot()'
        self.fields['histogram'].widget.attrs['class'] = 'beside-label'

        #List of values the current attribute can take
        if attributes.count() != 0:
            attribute = attributes[0]
            values = attribute.value_set.all()
            self.fields['values'] = forms.ModelMultipleChoiceField(values,
                    initial=values)
            self.fields['values'].widget.attrs['onchange'] = \
                    'update_topic_attribute_plot()'
            self.fields['values'].widget.attrs['class'] = 'under-label hideable'

        #The Select All button
        button = Button(onClick='highlight_all_topic_attribute_values(1)',
                        value='Select All')
        self.fields['select-all'] = forms.Field(label='', widget=button)

class TopicAttributeChart(object):
    """ A chart that plots nominally-valued attributes against topics"""
    form = TopicAttributePlotForm
    update_function = "update_topic_attribute_plot"

    def __init__(self, chart_parameters):
        """
        Initializes the chart, including initializing the chart data from the
        parameters.
        """
        self.chart_parameters = chart_parameters
        self.attribute = Attribute.objects.get(id=chart_parameters['attribute'])
        value_ids = chart_parameters['value'].split('.')
        self.values = Value.objects.filter(id__in=value_ids)
        topic_ids = chart_parameters['topic'].split('.')
        self.topics = Topic.objects.filter(id__in=topic_ids)
        self.frequency = 'frequency' in chart_parameters
        self.histogram = 'histogram' in chart_parameters
        self.chartdata = defaultdict(list)
        for value in self.values:
            if self.frequency:
                total_count = 1
            else:
                total_count = AttributeValue.objects.get(
                        attribute=self.attribute, value=value).token_count
            for topic in self.topics:
                try:
                    count = AttributeValueTopic.objects.get(value=value,
                            attribute=self.attribute, topic=topic).count
                except AttributeValueTopic.DoesNotExist:
                    count = 0
                self.chartdata[topic].append(float(count) / total_count)

    def get_chart_image(self):
        if self.histogram:
            return self.get_bar_chart()
        else:
            return self.get_line_chart()

    def get_source_data(self):
        return self.get_chart_json()
    
    def get_chart_json(self):

        thinned_labels = self.values
        labels = []
        for i in thinned_labels :
            labels.append(i.value)            
                            
        d = {}
        d['y-data'] = {}
        for topic in self.chartdata:                    
            d['y-data'].setdefault(topic.name, []).append(self.chartdata[topic])
                   
        d['x-data'] = [labels]              
        d['x-axis-label'] = self.attribute.name
        
        if self.frequency:
            d['y-axis-label'] = 'Frequency'
        else:
            d['y-axis-label'] = 'Percent' 
        
        return d         
        
    def get_bar_chart(self):
        """ Creates a Bar chart and writes it as a png, returning the data.
        
        Returns:
            The created png data.
        """
        fig = pylab.figure()

        sum_y = zeros(len(self.chartdata[self.topics[0]]))
        correlated_colors = dict(zip(self.chartdata,
                plotting_colors[:len(self.chartdata)]))
        for topic in self.chartdata:
            pylab.bar(range(0, len(self.values)), self.chartdata[topic],
                    label=topic.name, bottom=sum_y,
                    color=correlated_colors[topic])
            sum_y = [sum_y[i] + self.chartdata[topic][i]
                    for i in range(0, len(self.chartdata[topic]))]

        pylab.legend(loc=0)
        pylab.xlabel(self.attribute.name)
        if self.frequency:
            pylab.ylabel('Frequency')
        else:
            pylab.ylabel('Percent')
        thinned_labels = self.values
        if len(self.values) > 30:
            thinned_labels = thin_labels(self.values, len(self.values) / 30)
        pylab.xticks(arange(len(self.values)), thinned_labels, rotation=90,
                size='small')

        bar_chart_image = StringIO.StringIO()
        fig.canvas.print_figure(bar_chart_image, dpi=80)
        return bar_chart_image.getvalue()

    def get_line_chart(self):
        """
        Creates a Line chart based on the contents of chart_topics and
        chart attribute, writing the output as a png.
        
        """
        fig = pylab.figure()

        thinned_labels = self.values

        if len(self.values) > 30:
            thinned_labels = thin_labels(self.values, len(self.values) / 30)
        for topic in self.chartdata:
            pylab.plot(range(len(self.values)), self.chartdata[topic],
                label=topic.name)
        pylab.xticks(arange(len(self.values)), thinned_labels, rotation=90,
                size='small')

        pylab.legend(loc=0)
        pylab.xlabel(self.attribute)
        if self.frequency:
            pylab.ylabel('Frequency')
        else:
            pylab.ylabel('Percent')
        line_chart_image = StringIO.StringIO()
        fig.canvas.print_figure(line_chart_image, dpi=80)
        return line_chart_image.getvalue()

    def get_csv_file(self):
        csv_file = StringIO.StringIO()
        topics = list(self.chartdata.keys())
        values = list(self.values)

        writer = csv.writer(csv_file)
        writer.writerow(["value"] + topics)
        for i, value in enumerate(values):
            writer.writerow([value] + [self.chartdata[t][i] for t in topics])

        return csv_file.getvalue()

# Topic Metric Classes
######################

class TopicMetricForm(forms.Form):

    def __init__(self, dataset, analysis, *args, **kwargs):
        super(TopicMetricForm, self).__init__(*args, **kwargs)

        metrics = analysis.topicmetric_set.all()
        first = None
        second = None
        if metrics.count() != 0:
            first = metrics[0]
            if metrics.count() > 1:
                second = metrics[1]
        self.fields['first_metric'] = forms.ModelChoiceField(metrics,
                initial=first)
        self.fields['first_metric'].widget.attrs['onchange'] = \
                'update_topic_metric_plot()'
        self.fields['second_metric'] = forms.ModelChoiceField(metrics,
                initial=second)
        self.fields['second_metric'].widget.attrs['onchange'] = \
                'update_topic_metric_plot()'
        self.fields['linear_fit'] = forms.BooleanField(required=False)
        self.fields['linear_fit'].widget.attrs['onchange'] = \
                'update_topic_metric_plot()'


class TopicMetricChart(object):
    """A chart that plots one TopicMetric vs. another TopicMetric"""
    form = TopicMetricForm
    update_function = "update_topic_metric_plot"

    def __init__(self, chart_parameters):
        self.analysis = Analysis.objects.get(name=chart_parameters['analysis'],
                dataset__name=chart_parameters['dataset'])
        first_metric_id = chart_parameters['first_metric']
        self.first_metric = TopicMetric.objects.get(pk=first_metric_id)
        second_metric_id = chart_parameters['second_metric']
        self.second_metric = TopicMetric.objects.get(pk=second_metric_id)
        self.linear_fit = 'linear_fit' in chart_parameters

    def get_chart_image(self):
        fig = pylab.figure()

        x = []
        y = []
        for topic in self.analysis.topic_set.all():
            x.append(topic.topicmetricvalue_set.get(
                    metric=self.first_metric).value)
            y.append(topic.topicmetricvalue_set.get(
                    metric=self.second_metric).value)
        pylab.scatter(x, y, label='Topics')
        if self.linear_fit:
            slope, intercept, r, _p, _s_err = stats.linregress(x, y)
            line_x = [min(x), max(x)]
            line_y = [slope * point + intercept for point in line_x]
            pylab.plot(line_x, line_y, label='Linear fit, R: %.3f' % r)

        pylab.legend(loc=0)
        pylab.xlabel(self.first_metric.name)
        pylab.ylabel(self.second_metric.name)
        chart_image = StringIO.StringIO()
        fig.canvas.print_figure(chart_image, dpi=80)
        return chart_image.getvalue()


# NumericalAttributes-Distribution Classes
##########################################

class NumericAttributeDistributionPlotForm(forms.Form):

    def __init__(self, dataset, analysis, *args, **kwargs):
        """Create a Topics-Attribute plot form

        If there are any args, we assume the first is the POST request.
        """
        super(NumericAttributeDistributionPlotForm, self).__init__(*args, **kwargs)

        attributes = dataset.attribute_set.all()
        self.fields['attribute'] = forms.ModelMultipleChoiceField(attributes,
                initial=[attributes[0]])

        # A bunch of options to control what gets renered and how
        self.fields['by_frequency'] = forms.BooleanField(required=False)
        self.fields['histogram'] = forms.BooleanField(required=False, initial=True)
        self.fields['normalized'] = forms.BooleanField(required=False, initial=True)
        self.fields['kde'] = forms.BooleanField(required=False, initial=False)
        self.fields['points'] = forms.BooleanField(required=False, initial=False)


class NumericalAttributesDistributionChart(Chart):

    form = NumericAttributeDistributionPlotForm

    def __init__(self, chart_parameters):
        """
        Initializes the chart, including initializing the chart data from the
        parameters.
        """
        super(NumericalAttributesDistributionChart, self).__init__(
                chart_parameters)

        self.dataset = Dataset.objects.get(name=chart_parameters['dataset'])
        if chart_parameters['attribute']:
            attribute_ids = chart_parameters['attribute'].split('_')
            self.attributes = Attribute.objects.filter(id__in=attribute_ids)
        else:
            self.attributes = Attribute.objects.filter(dataset=self.dataset)[:1]

        self.chartdata = self.get_chart_data(self.dataset, self.attributes)

        # Extract the boolean variables
        self.histogram = False
        if ('histogram' in self.chart_parameters
                and self.chart_parameters['histogram']):
            self.histogram = True
        self.normalized = True
        if ('frequency' in self.chart_parameters
                and self.chart_parameters['frequency']):
            self.normalized = False
        self.kde = False
        if ('kde' in self.chart_parameters
                and self.chart_parameters['kde']):
            self.kde = True
        self.points = False
        if ('points' in self.chart_parameters
                and self.chart_parameters['points']):
            self.points = True

    def get_chart_data(self, dataset, attributes):
        chartdata = {}
        self.maxval = 0
        self.minval = 100000000
        for attribute in attributes:
            chartdata[attribute.name] = []
            # Until we have numerical attributes implemented, here's a hack
            # TODO(dan): fix this!
            try:
                for value in Value.objects.filter(attribute=attribute):
                    float_value = float(value.value)
                    if float_value > self.maxval:
                        self.maxval = float_value
                    if float_value < self.minval:
                        self.minval = float_value
                    chartdata[attribute.name].append(float_value)
            except:
                print('Warning: could not parse attribute {0} values'
                      ' as numbers.'.format(attribute.name))
        return chartdata

    def get_chart_image(self):

        fig = pylab.figure()

        for attribute in self.chartdata:
            if self.histogram:
                try:
                    pylab.hist(self.chartdata[attribute],
                               bins=100,
                               normed=self.normalized)
                except:
                    print("Warning: problem rendering attribute histogram graph.")
                    print(self.chartdata[attribute])
            if self.points:
                try:
                    pylab.scatter(self.chartdata[attribute], zeros(len(self.chartdata[attribute])))
                except:
                    print("Warning: problem rendering attribute distribution scattar graph.")
            if self.kde:
                try:
                    x_axis = linspace(self.minval, self.maxval, 1000)
                    approx_dist = gaussian_kde(self.chartdata[attribute])
                    pylab.plot(x_axis, approx_dist(x_axis))
                except:
                    print("Warning: problem rendering attribute distribution kde graph.")
                    print("min: " + str(self.minval) + ", max: " + str(self.maxval))
                    print("linspace:" + x_axis)

        chart_image = StringIO.StringIO()
        fig.canvas.print_figure(chart_image, dpi=80)
        return chart_image.getvalue()


# This has to be down here, after everything has been defined
# The format is this: '[name of plot]': (class of plot, order in list)
plot_types = { 'Topics vs. Attributes': (TopicAttributeChart, 1),
        #'NumericalAttribute-Distribution': NumericalAttributesDistributionChart,
#        'Topic Metric Comparison': (TopicMetricChart, 2),
        }


# vim: et sw=4 sts=4
