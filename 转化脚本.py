import os
import pandas as pd
import json
import time
import numpy as np


nodes=pd.read_excel('nodes.xls',index_col=False)
edges=pd.read_excel('edges.xls',index_col=False)

nodes_dict=dict(zip(nodes['id'],nodes['text']+'_'+nodes['id'].astype(str)))
edges['目标名称']=edges['source'].apply(lambda x:nodes_dict[x])
edges['关联目标']=edges['target'].apply(lambda x:nodes_dict[x])
edges['目标类型']=edges['目标名称'].apply(lambda x:x.split('_')[0])
edges['关联关系类型']=edges['labels']
raw=edges[['目标类型','目标名称','关联目标','关联关系类型']]

raw.to_excel('raw.xls',index=False,engine='openpyxl')