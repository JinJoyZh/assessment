#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Author jinqi

import tornado.ioloop
import tornado.web
import os
import pandas as pd
import json
from assess import process_data
import time
import warnings
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
            all_file=os.listdir('./')
            nodes_file=[i for i in all_file if i.endswith('nodes.xls')]
            max_time=pd.to_datetime(pd.Series([i[:-10] for i in nodes_file if len(i)>10]),format='%Y-%m-%d-%H_%M_%S').max()
            if pd.isna(max_time):
                if 'nodes.xls' in nodes_file:
                    nodes=pd.read_excel(os.path.join(path,'nodes.xls'),index_col=False)
                else:
                    print('不存在nodes.xls,结束')
                    exit()
            else:
                nodes=pd.read_excel(os.path.join(path,max_time.strftime("%Y-%m-%d-%H_%M_%S")+'_nodes.xls'),index_col=False)

            edges_file=[i for i in all_file if i.endswith('edges.xls')]  
            max_time=pd.to_datetime(pd.Series([i[:-10] for i in edges_file if len(i)>10]),format='%Y-%m-%d-%H_%M_%S').max()
            if pd.isna(max_time):
                if 'edges.xls' in edges_file:
                    edges=pd.read_excel(os.path.join(path,'edges.xls'),index_col=False)
                else:
                    print('不存在edges.xls,结束')
                    exit()
            else:
                edges=pd.read_excel(os.path.join(path,max_time.strftime("%Y-%m-%d-%H_%M_%S")+'_edges.xls'),index_col=False)

            nodes['attrs']=nodes['color'].apply(lambda x:{"body": {"fill": x}})
            del nodes['color']
            edges['attrs']=edges['attrs'].apply(lambda x:{"line": {"stroke": x}})
            edges['labels']=edges['labels'].apply(lambda x:[{'attrs': {'text': {'text': x}}}])
            GlobalVars.set('nodes', nodes)
            GlobalVars.set('edges', edges)
            return 1
        except:
            return 0


    def dataframe_to_json(self):
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            # if isinstance(edges['labels'].iloc[0],str):
            #     edges['labels']=edges['labels'].apply(lambda x:eval(x))
            #     edges['attrs']=edges['attrs'].apply(lambda x:eval(x))
            #     nodes['attrs']=nodes['attrs'].apply(lambda x:eval(x))
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

            nodes['color']=nodes['attrs'].apply(lambda x:x['body']['fill'])
            del nodes['attrs']
            edges['attrs']=edges['attrs'].apply(lambda x:x["line"]["stroke"])
            edges['labels']=edges['labels'].apply(lambda x:x[0]['attrs']['text']['text'])

            nodes.to_excel(os.path.join(path,time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time()))+'_nodes.xls'),index=False)
            edges.to_excel(os.path.join(path,time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time()))+'_edges.xls'),index=False)

            return 1
        except:
            return 0

    def update_node(self,new_node_str):
        nodes=GlobalVars.get('nodes')
        try:
            # print(new_node_str)
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
            path=self.get_argument('path')
            if path == '':
                assessment = self.assess()
            else:
                assessment = self.assess(path)
            if assessment == {}:
                result = {'result': 0}
            else:
                result = {'result': 1,
                          'content': assessment}
                result = json.dumps(result, ensure_ascii=False)
            self.finish(result)

    def assess(self, path=os.path.abspath(os.path.dirname(__file__))):
        edge_xls_path = os.path.join(path,'edges.xls')
        assessment = {}
        try:
            assessment = process_data(edge_xls_path)
        except Exception as e:
            print(e)
            return assessment
        return assessment

 
if __name__ == "__main__":

    application = tornado.web.Application([(r"/read", MainHandler),
        (r"/save", MainHandler),
        (r"/update", MainHandler),
        (r"/delete", MainHandler),
        (r"/assess", MainHandler)])
    application.listen(8833)
    tornado.ioloop.IOLoop.instance().start()