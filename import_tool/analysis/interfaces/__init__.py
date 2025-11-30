from .mallet_analysis import MalletLdaAnalysis, MalletHldaAnalysis
from .random_analysis import RandomAnalysis
from .bertopic_analysis import BertopicAnalysis

analyses = {
    "MalletLDA": MalletLdaAnalysis,
    "MalletHLDA": MalletHldaAnalysis,
    "Random": RandomAnalysis,
    "BERTopic": BertopicAnalysis,
}
