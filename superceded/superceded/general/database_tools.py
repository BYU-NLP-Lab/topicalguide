#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from topic_modeling.visualize.models import (Dataset, Analysis)

def get_dataset_model(dataset_name):
    return Dataset.objects.get(name=dataset_name)

def get_analysis_model(analysis_name, dataset_name):
    return Analysis.objects.get(name=analysis_name, dataset__name=dataset_name)


# vim: et sw=4 sts=4
