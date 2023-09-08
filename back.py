#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Author jinqi

# 运行
# python back.py

# 读取csv文件，文件与该脚本放在同个文件夹下，成功返回json文本，失败返回0.
# 无需参数，默认同目录下
# http://127.0.0.1:8833/read?func=read&path
# 传入路径
# http://127.0.0.1:8833/read?func=read&path=C:\Users\dhujq\Desktop\DB\my\脚本


# 修改节点（传入的new_node参数为str类型，一次只能改一个节点），成功返回1，失败返回0.
# fill无#,需要再次处理
# http://127.0.0.1:8833/update?func=update&new_node={"id":"S398","label":"S3","x":1,"y":1,"width":80,"height":40,"shape":"circle","text":"无人侦察机","attrs":{"body":{"fill":"FFA500"}}}


# 删除节点1，成功返回json文本，失败返回0.
# http://127.0.0.1:8833/delete?func=delete&node_id=S398

# 删除节点2,该节点有备份节点，成功返回json文本，失败返回0.
# http://127.0.0.1:8833/delete?func=delete&node_id=C22


# 保存结果，成功返回1，失败返回0.
# 无需参数，默认同目录下
# http://127.0.0.1:8833/save?func=save&path
# 传入路径
# http://127.0.0.1:8833/read?func=read&path=C:\Users\dhujq\Desktop\DB\my\脚本

import tornado.ioloop
import tornado.web
import os
import pandas as pd
import json
from assess import process_data

from util.csv_to_json import csv_to_json

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
            nodes=pd.read_csv(os.path.join(path,'nodes.csv'),index_col=0)
            edges=pd.read_csv(os.path.join(path,'edges.csv'),index_col=0)
            GlobalVars.set('nodes', nodes)
            GlobalVars.set('edges', edges)
            return 1
        except:
            return 0


    def dataframe_to_json(self):
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            edges['labels']=edges['labels'].apply(lambda x:eval(x))
            edges['attrs']=edges['attrs'].apply(lambda x:eval(x))
            nodes['attrs']=nodes['attrs'].apply(lambda x:eval(x))
            
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
            # _ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径
            nodes.to_csv(os.path.join(path,'nodes.csv'))
            edges.to_csv(os.path.join(path,'edges.csv'))
            return 1
        except:
            return 0

    def update_node(self,new_node_str):
        nodes=GlobalVars.get('nodes')
        # try:
        new_node=eval(new_node_str)
        print(new_node)
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
        # except:
        #     return 0
                
    def delete(self,delete):
        try:
            nodes=GlobalVars.get('nodes')
            edges=GlobalVars.get('edges')
            if len(edges.loc[(edges['labels']=={'attrs': {'text': {'text': 'backup'}}})&(edges['target']==delete)])>0:
                backup=edges.loc[(edges['labels']=={'attrs': {'text': {'text': 'backup'}}})&(edges['target']==delete),'source'].iloc[0]
                backup_edges=edges.loc[(edges['source']!=delete)&(edges['target']!=delete)&((edges['source']==backup)|(edges['target']==backup))]
                delete_edges=edges.loc[(edges['source']!=backup)&(edges['target']!=backup)&((edges['source']==delete)|(edges['target']==delete))]
                other_edges=edges.loc[(edges['source']!=backup)&(edges['target']!=backup)&(edges['source']!=delete)&(edges['target']!=delete)]
                delete_edges=delete_edges.replace(delete, backup)
                mo_edges=pd.concat([backup_edges,delete_edges])
                mo_edges=mo_edges.drop_duplicates()
                edges=pd.concat([mo_edges,other_edges])
                nodes=nodes.loc[nodes['id']!=delete]
            else:
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
            assessment = self.assess(path)
            if assessment == {}:
                result = {'result': 0}
            else:
                result = {'result': 1,
                          'content': assessment}
                result = json.dumps(result, ensure_ascii=False) 
            self.finish(result)


    def assess(self, path=os.path.abspath(os.path.dirname(__file__))):
        edge_path = os.path.join(path,'edges.csv')
        assessment = {}
        try:
            json_str = csv_to_json(edge_path)
            assessment = process_data(json_str)
        except Exception as e:
            print(e)
            return assessment
        return assessment
 
if __name__ == "__main__":
    # _ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径
    # nodes=pd.read_csv(os.path.join(_,'nodes.csv'),index_col=0)
    # edges=pd.read_csv(os.path.join(_,'edges.csv'),index_col=0)

    application = tornado.web.Application([(r"/read", MainHandler),
        (r"/save", MainHandler),
        (r"/update", MainHandler),
        (r"/delete", MainHandler),
        (r"/assess", MainHandler)])
    application.listen(8833)
    tornado.ioloop.IOLoop.instance().start()