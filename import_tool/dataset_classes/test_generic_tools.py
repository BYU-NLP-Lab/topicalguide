from __future__ import print_function

import os

from generic_tools import GenericTools


def test_metadata_to_dict():
    meta = """YEAR: 1983
MONTH: Nov.
SPEAKER: Marvin J. Ashton
CALLING: Of the Quorum of the Twelve Apostles
TOPIC: commitment"""
    meta_dict = GenericTools.metadata_to_dict(meta)
    
    actual_meta_dict = {'year': '1983', 'month': 'Nov.', 'speaker': 'Marvin J. Ashton',
                        'topic': 'commitment'}
    
    for key in actual_meta_dict:
        assert key in meta_dict
        assert meta_dict[key] == actual_meta_dict[key]

