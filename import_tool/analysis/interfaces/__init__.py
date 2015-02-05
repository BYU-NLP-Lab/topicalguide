from __future__ import division, print_function, unicode_literals
from mallet_analysis import MalletLdaAnalysis, MalletHldaAnalysis
from random_analysis import RandomAnalysis

analyses = {
    "MalletLDA": MalletLdaAnalysis,
    "MalletHLDA": MalletHldaAnalysis,
    "Random": RandomAnalysis,
}
