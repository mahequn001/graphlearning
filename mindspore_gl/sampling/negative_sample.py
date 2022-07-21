# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
""" negative_sample """
import random
from math import ceil
import numpy as np
import mindspore_gl.bucket_kernel

def negative_sample(positive, node, num_neg_samples, mode='undirected', re='more'):
    """
    Input all positive sample edge sets, and specify the negative sample length,
    and then return the negative sample edge set of the same length, and will not repeat the positive samples
    Can choose to consider self-loop, directed graph or undirected graph operation

    Args:
        positive(list or array):All positive sample edges,shape:(col_len, row_len)
        node(int): number of node
        num_neg_samples(int):Negative sample length
        mode(str): type of operation matrix
        re(str): type of input data

    Returns:
        array, Negative sample edge set,shape:(num_neg_samples, 2)

    Examples:
        >>> from mindspore_gl.sampling import negative_sample
        >>> positive = [[1,2],[2,3]]
        >>> neg_len = 4
        >>> neg = negative_sample(positive, 4, neg_len)
        >>> print(neg)
            [[0 3]
            [0 2]
            [1 3]
            [0 1]]
    """
    if not isinstance(positive, (list, np.ndarray)):
        raise TypeError("The positive data type is {},\
                        but it should be ndarray or list.".format(type(positive)))
    if not isinstance(node, int):
        raise TypeError("The node type is {},\
                        but it should be int.".format(type(node)))
    if not isinstance(num_neg_samples, int):
        raise TypeError("The num_neg_samples type is {},\
                        but it should be int.".format(type(num_neg_samples)))
    if not isinstance(mode, str):
        raise TypeError("The mode data type is {},\
                        but it should be str.".format(type(mode)))
    if not isinstance(re, str):
        raise TypeError("The re data type is {},\
                        but it should be str.".format(type(re)))

    def sample(population: int, k: int):
        """
        Randomly sample the edge set of length population,
        if the length is less than k, directly output all edges of length population
        """
        if population <= k:
            return np.arange(population)
        return random.sample(range(population), k)

    if re == 'more':
        positive = np.array([i for i in positive])
        row = np.array([i[0] for i in positive])
        col = np.array([i[1] for i in positive])
        size = positive.shape[0]
    else:
        positive = np.array(positive)
        row = np.array(positive[0])
        col = np.array(positive[1])
        size = positive.shape[1]

    idx, population = edge_index_to_vector([row, col], (node, node), mode=mode)

    if num_neg_samples is None:
        num_neg_samples = size
    if mode == 'undirected':
        num_neg = num_neg_samples
        num_neg_samples = ceil(num_neg_samples / 2)

    prob = 1. - size/(node*node - node)
    sample_size = int(1.1 * num_neg_samples / prob)
    neg_idx = None
    for _ in range(3):
        rnd = np.array(sample(population, sample_size))
        mask = np.isin(rnd, idx)
        if neg_idx is not None:
            mask |= np.isin(rnd, neg_idx)
        rnd = rnd[~mask]
        neg_idx = rnd if neg_idx is None else np.concatenate([neg_idx, rnd])
        if len(neg_idx) >= num_neg_samples:
            neg_idx = neg_idx[:num_neg_samples]
            break
    assert num_neg_samples == neg_idx.shape[0]
    neg_idx = vector_to_edge_index(neg_idx, (node, node), mode=mode)

    if re == 'more':
        idx = np.array([[neg_idx[0][i], neg_idx[1][i]] for i in range(num_neg)])
    else:
        idx = neg_idx
    return idx

def edge_index_to_vector(edge_index, size, mode='undirected'):
    """
    Convert the edge to the corresponding number,
    you can specify whether to consider the processing method of the diagonal matrix,
    the processing method of the directed graph or the processing method of the undirected graph

    Args:
        edge_index(list):set of two edges，shape:(row_len or col_len, 2)
        size(tuple):number of graph nodes, shape:(node, node)
        mode(str):type of operation matrix

    Returns:
        idx(array): Transformed vector,shape:(1, row_len or col_len)
        population(int): number of edges to sample

    Examples:
        >>> from mindspore_gl.sampling import edge_index_to_vector
        >>> import numpy as np
        >>> idx, population =  edge_index_to_vector(np.array([[0, 0, 1],[1, 2, 2]]), (3,3))
        >>> print(idx, population)
            [0 1 2] 3
    """
    if not isinstance(edge_index, list):
        raise TypeError("The edge_index data type is {},\
                        but it should be list.".format(type(edge_index)))
    if not isinstance(size, tuple):
        raise TypeError("The size data type is {},\
                        but it should be tuple.".format(type(size)))
    if not isinstance(mode, str):
        raise TypeError("The mode data type is {},\
                        but it should be str.".format(type(mode)))
    assert size[0] == size[1]

    if mode == 'bipartite':
        row, col = edge_index

        idx = (row * size[1]) + col
        population = size[0] * size[1]

    elif mode == 'undirected':
        row, col = edge_index
        num_nodes = size[0]
        mask = row <= col
        row, col = row[mask], col[mask]
        offset = np.arange(1, num_nodes).cumsum(0)[row]
        idx = row*(num_nodes) + col - offset
        population = (num_nodes * (num_nodes + 1)) // 2 - num_nodes

    else:
        row, col = edge_index
        num_nodes = size[0]

        mask = row != col
        row, col = row[mask], col[mask]
        col[row < col] -= 1
        idx = row*(num_nodes - 1) + col
        population = num_nodes * num_nodes - num_nodes

    return idx, population

def vector_to_edge_index(idx, size, mode='undirected'):
    """
    Convert the number to the corresponding edge,
    you can specify whether to consider the processing method of the diagonal matrix,
    the processing method of the directed graph or the processing method of the undirected graph

    Args:
        idx(ndarray):collection of edges，shape:(1, row_len or col_len)
        size(tuple):number of graph nodes, shape:(node, node)
        mode(str):type of operation matrix

    Returns:
        array, transformed edge, shape:(row_len or col_len, 2)

    Examples:
        >>> from mindspore_gl.sampling import vector_to_edge_index
        >>> import numpy as np
        >>> idx = vector_to_edge_index(np.array([0, 1, 2]), (3, 3))
        >>> print(idx)
            [[0 0 1]
            [1 2 2]]
    """
    if not isinstance(idx, np.ndarray):
        raise TypeError("The idx data type is {},\
                        but it should be ndarray.".format(type(idx)))
    if not isinstance(size, tuple):
        raise TypeError("The size data type is {},\
                        but it should be tuple.".format(type(size)))
    if not isinstance(mode, str):
        raise TypeError("The mode data type is {},\
                        but it should be str.".format(type(mode)))
    def bucketize(i, v):
        """
        Divide y into intervals and return the number of intervals in y for each element in x.
        """
        i = list(i)
        v = list(v)
        l = len(i)
        n = len(v)
        res = mindspore_gl.bucket_kernel.bucket(i, v, l, n)
        return res

    assert size[0] == size[1]

    if mode == 'bipartite':
        row = np.round(idx / size[1])
        col = idx % size[1]
        idx = np.stack([row, col], dim=0)
    elif mode == 'undirected':
        num_nodes = size[0]
        offset = np.arange(1, num_nodes).cumsum(0)
        offset1 = np.arange(1, num_nodes)[::-1].cumsum(0)
        row = bucketize(offset1, idx)
        col = (offset[row] + idx) % num_nodes
        a, b = np.concatenate([row, col]), np.concatenate([col, row])
        idx = np.stack([a, b])
    else:
        num_nodes = size[0]
        row = np.floor(idx / (num_nodes - 1))
        col = idx % (num_nodes - 1)
        col[row <= col] += 1
        idx = np.stack([row, col])
    return idx
