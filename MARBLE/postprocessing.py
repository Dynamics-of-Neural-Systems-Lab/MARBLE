#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .lib import plotting
from .lib import geometry as g
import numpy as np
import matplotlib.pyplot as plt

def postprocessing(data,
                   cluster_typ='kmeans', 
                   embed_typ='umap', 
                   n_clusters=15, 
                   manifold=None,
                   seed=0):
    """
    Cluster embedding and return distance between clusters
    
    Returns
    -------
    data : PyG data object containing .emb attribute, a nx2 matrix of embedded data
    clusters : sklearn cluster object
    dist : cxc matrix of pairwise distances where c is the number of clusters
    
    """

    emb = data.emb
    
    #k-means cluster
    clusters = g.cluster(emb, cluster_typ, n_clusters, seed)
    clusters = g.relabel_by_proximity(clusters)
    clusters['slices'] = data._slice_dict['x']
    
    #compute distances between clusters
    dist, gamma, cdist = g.compute_histogram_distances(clusters)
    
    #embed into 2D via t-SNE for visualisation
    emb = np.vstack([emb, clusters['centroids']])
    emb, manifold = g.embed(emb, embed_typ, manifold)  
    emb, clusters['centroids'] = emb[:-n_clusters], emb[-n_clusters:]
    
    #store everything in data
    data.emb_2d = emb
    data.manifold = manifold
    data.clusters = clusters
    data.dist = dist
    data.gamma = gamma
    data.cdist = cdist
    
    return data


def compare_attractors(data, source_target):
    
    assert hasattr(data, ('emb_2d', )), 'No clusters found. First, run \
        geometry.cluster(data) or postprocessing(data)!'
    
    s, t = source_target
    slices = data._slice_dict['x']
    n_slices = len(slices)-1
    s_s = range(slices[s], slices[s+1])
    s_t = range(slices[t], slices[t+1])
    
    assert s<n_slices-2 and t<n_slices-1, 'Source and target must be < number of slices!'
    assert s!=t, 'Source and target must be different!'
    
    _, ax = plt.subplots(1, 3, figsize=(10,5))
    
    #color code features
    gammadist = data.gamma[s,t,...]*data.cdist
    np.fill_diagonal(gammadist, 0.0)
    
    c = gammadist.sum(1)
    cluster_ids = set(data.clusters['labels'][s_s])
    labels = [i for i in s_s]
    for cid in cluster_ids:
        idx = np.where(cid==data.clusters['labels'][s_s])[0]
        for i in idx:
            labels[i] = c[cid]
    
    plotting.embedding(data.emb_2d, ax=ax[0], alpha=0.05)
    plotting.embedding(data.emb_2d[s_s], labels=labels, ax=ax[0], alpha=1.)
    prop_dict = dict(style='>', node_feature=labels, lw=2, arrowhead=.1, \
                           axis=False, alpha=1.)
    plotting.trajectories(data.pos[s_s], data.x[s_s], ax=ax[1], **prop_dict)
        
    c = gammadist.sum(0)
    cluster_ids = set(data.clusters['labels'][s_t])
    labels = [i for i in s_t]
    for cid in cluster_ids:
        idx = np.where(cid==data.clusters['labels'][s_t])[0]
        for i in idx:
            labels[i] = -c[cid]
    
    plotting.embedding(data.emb_2d[s_t], labels=labels, ax=ax[0], alpha=1.)
    plotting.trajectories(data.pos[s_t], data.x[s_t], ax=ax[2],**prop_dict)