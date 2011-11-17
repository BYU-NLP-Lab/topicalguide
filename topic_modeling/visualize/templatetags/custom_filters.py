#!/usr/bin/env python

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


from django import forms, template

register = template.Library()

@register.filter
def divide(value, arg):
    value = float(value)
    arg = float(arg)
    if arg == 0:
        return 'Error, divide by 0'
    else:
        return '%.2f' % (value/arg)

@register.filter
def formatmetric(value, arg):
    value = float(value)
    arg = int(arg)
    if value % 1 == 0.0:
        return str(int(value))
    fmt_str = '%%.%df' % arg
    return fmt_str % value


# vim: et sw=4 sts=4
