from __future__ import division, print_function, unicode_literals
from mallet_analysis import MalletLdaAnalysis, MalletHldaAnalysis
from mallet_itm_analysis import MalletItmAnalysis
from random_analysis import RandomAnalysis

analyses = {
    "MalletITM": MalletItmAnalysis,
    "MalletLDA": MalletLdaAnalysis,
    "MalletHLDA": MalletHldaAnalysis,
    "Random": RandomAnalysis,
}
