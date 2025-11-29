from .generic_dataset import GenericDataset
from .json_dataset import JsonDataset
from .random_dataset import RandomDataset

datasets = {
    'Generic': GenericDataset,
    'JSON': JsonDataset,
    'Random': RandomDataset,
}
