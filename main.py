#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Author jinqi

import tornado.ioloop
import tornado.web
import os
import pandas as pd
import json
from assess import process_data, construct_directed_graph
import time
import warnings
import networkx as nx
import numpy as np

from indicator.constribution import identify_critical_nodes
warnings.filterwarnings('ignore')



class GlobalVars:
    _data = {}

    @classmethod
    def set(cls, key, value):
        cls._data[key] = value

    @classmethod
    def get(cls, key):
        return cls._data.get(key)

    @classmethod
    def delete(cls, key):
        if key in cls._data:
            del cls._data[key]




class MainHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')


    def read(self,path=os.path.abspath(os.path.dirname(__file__))):
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            if nodes is not None:
                GlobalVars.set("previous_nodes", nodes)
                GlobalVars.set("previous_edges", edges)
            if path=='':
                path='./'
            all_file=os.listdir(path)
            file=[i for i in all_file if i.endswith('raw.xls')]
            max_time=pd.to_datetime(pd.Series([i[:-8] for i in file if len(i)>7]),format='%Y-%m-%d-%H_%M_%S').max()
            if pd.isna(max_time):
                if 'raw.xls' in file:
                    raw=pd.read_excel(os.path.join(path,'raw.xls'),index_col=False)
                else:
                    print('不存在raw.xls,结束')
                    exit()
            else:
                raw=pd.read_excel(os.path.join(path,max_time.strftime("%Y-%m-%d-%H_%M_%S")+'_raw.xls'),index_col=False)

            nodes_list=list(set(raw['目标名称'])|set(raw['关联目标']))
            nodes_dict=dict([(int(i.split('_')[1]),i.split('_')[0]) for i in nodes_list])
            nodes=pd.DataFrame(nodes_dict.items(),columns=['id','labels'])
            nodes=nodes.sort_values('id')
            nodes.reset_index(inplace=True,drop=True)
            nodes['text']=nodes['labels']
            nodes['x']=np.random.randint(0, 1000, size=len(nodes))
            nodes['y']=np.random.randint(0, 1000, size=len(nodes))
            nodes['width']=80
            nodes['width']=40
            nodes['shape']='circle'
            nodes['isReserved']=0
            nodes['attrs']='#000000'
            nodes['attrs']=nodes['attrs'].apply(lambda x:{"body": {"fill": x}})

            edges=raw.copy()
            edges['source']=edges['目标名称'].apply(lambda x:int(x.split('_')[-1]))
            edges['target']=edges['关联目标'].apply(lambda x:int(x.split('_')[-1]))
            edges['text']=edges['关联关系类型']
            edges['labels']=edges['关联关系类型']
            edges['labels']=edges['labels'].apply(lambda x:[{'attrs': {'text': {'text': x}}}])
            edges['attrs']='#000000'
            edges['attrs']=edges['attrs'].apply(lambda x:{"line": {"stroke": x}})
            nodes.loc[nodes['id'].isin(set(edges.loc[edges['text']=='备份','source'])),'isReserved']=1
            edges=edges[['source','target','text','labels','attrs']]

            GlobalVars.set('nodes', nodes)
            GlobalVars.set('edges', edges)
            return 1
        except:
            return 0



    def dataframe_to_json(self):
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            nodes_json=nodes.to_json(orient="records")
            edges_json=edges.to_json(orient="records")
            result=json.dumps({'nodes':eval(nodes_json),'edges':eval(edges_json)})
            return result
        except:
            return 0
        
    def save(self,path=os.path.abspath(os.path.dirname(__file__))):
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')

            nodes_dict=dict(zip(nodes['id'],nodes['text']+'_'+nodes['id'].astype(str)))
            edges['目标名称']=edges['source'].apply(lambda x:nodes_dict[x])
            edges['关联目标']=edges['target'].apply(lambda x:nodes_dict[x])
            edges['目标类型']=edges['目标名称'].apply(lambda x:x.split('_')[0])
            edges['关联关系类型']=edges['labels'].apply(lambda x:x[0]['attrs']['text']['text'])
            raw=edges[['目标类型','目标名称','关联目标','关联关系类型']]

            raw.to_excel(os.path.join(path,time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time()))+'_raw.xls'),
                index=False,engine='openpyxl')
            return 1
        except:
            return 0

    def update_node(self,new_node_str):
        nodes=GlobalVars.get('nodes')
        try:
            new_node=json.loads(new_node_str)
            if new_node['id'] not in set(nodes['id']):
                return 0
            else:
                update_index=nodes.loc[nodes['id']==new_node['id']].index
                if len(update_index)==1:
                    nodes.loc[update_index]=[new_node[key] for key in nodes.columns]
                    GlobalVars.set('nodes', nodes)
                    return 1
                else:
                    return 0
        except:
            return 0


    def delete(self,delete):
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            GlobalVars.set("previous_nodes", nodes)
            GlobalVars.set("previous_edges", edges)
            delete=int(delete)
            if len(edges.loc[(edges['text']=='reserved')&(edges['target']==delete)])>0:
                reserved=edges.loc[(edges['text']=='reserved')&(edges['target']==delete),'source'].iloc[0]
                edges=edges.loc[~((edges['text']=='reserved')&((edges['source']==reserved)|(edges['target']==delete)))]
                edges=edges.replace(delete,reserved)
                edges=edges.drop_duplicates(subset=['source','target','text'])
                nodes=nodes[nodes['id']!=reserved]
                nodes.loc[nodes['id']==delete,'id']=reserved
            elif len(edges.loc[(edges['text']=='replace')&(edges['target']==delete)])>0:
                replace=edges.loc[(edges['text']=='replace')&(edges['target']==delete),'source'].iloc[0]
                replace_edges=edges.loc[(edges['source']!=delete)&(edges['target']!=delete)&((edges['source']==replace)|(edges['target']==replace))]
                delete_edges=edges.loc[(edges['source']!=replace)&(edges['target']!=replace)&((edges['source']==delete)|(edges['target']==delete))]
                other_edges=edges.loc[(edges['source']!=replace)&(edges['target']!=replace)&(edges['source']!=delete)&(edges['target']!=delete)]
                delete_edges=delete_edges.replace(delete, replace)
                mo_edges=pd.concat([replace_edges,delete_edges])
                edges=pd.concat([mo_edges,other_edges])
                edges=edges.drop_duplicates(subset=['source','target','text'])
                nodes=nodes[nodes['id']!=delete]
            else:
                print('非reserved && 非replace')
                nodes=nodes.loc[nodes['id']!=delete]
                edges=edges.loc[(edges['target']!=delete)&(edges['source']!=delete)]
            GlobalVars.set('nodes', nodes)
            GlobalVars.set('edges', edges)
            json_result = self.dataframe_to_json()
            return json_result
        except:
            return 0



    def get(self):
        """get请求"""
        func = self.get_argument('func')
        if func=='read':
            path=self.get_argument('path')
            if self.read(path):
                json_result=self.dataframe_to_json()
                self.finish({'result': json_result})
        if func=='save':
            path=self.get_argument('path')
            result=self.save(path)
            self.finish({'result': result})
        if func=='update':
            new_node_str=self.get_argument('new_node')
            result=self.update_node(new_node_str)
            self.finish({'result': result})
        if func=='delete':
            node_id=self.get_argument('node_id')
            result=self.delete(node_id)
            self.finish({'result': result})
        if func=='assess':
            assessment = self.assess()
            if assessment == {}:
                result = {"result": 0}
            else:
                result = {"result": 1,
                          "content": assessment}
                result = json.dumps(result, ensure_ascii=False)
            self.finish(result)
        if func=='critical_nodes':
            threshold = self.get_argument('threshold')
            threshold = float(threshold)
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            is_success = self.compute_contributions(nodes, edges, threshold)
            if is_success:
                json_result=self.dataframe_to_json()
                self.finish({'result': json_result})
        if func=='efficacy_change':
            threshold = self.get_argument('threshold')
            threshold = float(threshold)
            efficacy_change = self.compute_efficacy_change(threshold)
            if efficacy_change != float('inf'):
                result = {
                    "效能变化": efficacy_change
                }
                result = json.dumps(result, ensure_ascii=False)
                self.finish(result)
            
    def assess(self):
        assessment = {}
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            assessment = process_data(nodes, edges)
        except Exception as e:
            print(e)
            return assessment
        return assessment
    
    def compute_contributions(self, nodes, edges, threshold = 0.0):
        if (nodes is None) or (edges is None):
            return 0
        G = construct_directed_graph(nodes, edges)
        # 识别关键节点
        critical_marks, contribution_list = identify_critical_nodes(G, threshold)
        total_score = 0
        for v in contribution_list:
            total_score += v
        nodes["contribution"] = contribution_list
        nodes["is_critical"] = critical_marks
        return sum(nodes["contribution"])
    
    def compute_efficacy_change(self, threshold = 0.0):
        previous_nodes = GlobalVars.get('previous_nodes')
        previous_edges = GlobalVars.get('previous_edges')
        if previous_nodes is None:
            return float('inf') 
        nodes = GlobalVars.get("nodes")
        edges = GlobalVars.get("edges")
        previous_efficacy = self.compute_contributions(previous_nodes, previous_edges, threshold) 
        current_efficacy = self.compute_contributions(nodes, edges, threshold) 
        efficacy_change = current_efficacy - previous_efficacy
        efficacy_change = round(efficacy_change, 3)
        return efficacy_change


if __name__ == "__main__":

    application = tornado.web.Application([(r"/read", MainHandler),
        (r"/save", MainHandler),
        (r"/update", MainHandler),
        (r"/delete", MainHandler),
        (r"/assess", MainHandler)])
    application.listen(8833)
    tornado.ioloop.IOLoop.instance().start()
