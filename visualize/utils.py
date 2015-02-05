from __future__ import division, print_function, unicode_literals
import random


def reservoir_sample(sample_size, data_count, seed=None):
    """
    This function takes the desired sample size and the number of items in a dataset
    and uses resevoir sampling to return a list of sampled indices from that dataset.
    sample_size -- the number of items to sample
    data_count -- the number of items that can be indexed, that is, the size of the dataset
    seed -- seeds the random number generator
    """
    random.seed(seed)
    sample_indices = []

    for index in xrange(data_count):
        # Generate the reservoir
        if index < sample_size:
            sample_indices.append(index)
        else:
            # Randomly replace elements in the reservoir
            # with a decreasing probability.
            # Choose an integer between 0 and index (inclusive)
            r = random.randint(0, index)
            if r < sample_size:
                sample_indices[r] = index

    return sample_indices
