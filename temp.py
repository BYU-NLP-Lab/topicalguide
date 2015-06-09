

from import_tool.analysis.interfaces import mallet_itm_analysis

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'topicalguide.settings'

mallet_itm_analysis.main()

