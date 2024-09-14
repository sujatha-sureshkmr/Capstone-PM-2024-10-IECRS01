import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO
from PIL import UnidentifiedImageError 
import os
import networkx as nx
import matplotlib.pyplot as plt

class aienginmodelbuild:
    def __init__(self, datafile_df,kgdatafilename):
        self.datafilename = datafile_df
        self.kgdatafilename =kgdatafilename

    def datapreparation(self):
        df1 = self.datafilename
        #print('dp - step 1')
        #print('datapreparation - df1',df1.shape)
        print(df1['image_name'].head(),df1['ocr_det_arr'].head())
        df = df1[df1['image_name'].notnull()& df1['ocr_det_arr'].notnull()]
        df.loc[:, 'Text'] = 'Component - ' + df['Text'].astype(str)
        #print('datapreparation - df knowledge_graph',df.shape)
        #print('dp - step 2')
        #df.loc[:, 'cc_segment_image'] = df['cc_segment_image'].replace(['', None], pd.NA)
        #df.loc[:, 'cc_segment_image'] = df['cc_segment_image'].fillna(df['image_name'])
        #print('dp - step 3')
        header_cols = [col for col in df.columns if col.startswith('Header_')]
        #print('header_cols',header_cols)
        # Sort 'Header_' columns numerically
        header_cols.sort(key=lambda x: int(x.split('_')[1]) if x.split('_')[1].isdigit() else float('inf'))
        #print('dp - step 4')
        # Reorder the columns with 'Header_' columns first, followed by 'Header_image', and then 'Text'
        new_cols_order = header_cols + ['Text'] + ['cc_segment_image']
        #print('new_cols_order',new_cols_order)
        new_cols_order.remove('Header_style')
        
        filtered_df = df[new_cols_order]

        filtered_df = filtered_df.dropna(axis=1, how='all')
        print('filtered_df',filtered_df.columns)
        
        if not filtered_df.empty:
            self.knowledge_graph(filtered_df)
        return filtered_df
    
    def knowledge_graph(self,filtered_df):
        #knowledgedbgraph=[]
        if not os.path.exists(self.kgdatafilename):
            os.makedirs(self.kgdatafilename)
            print(f"Directory '{self.kgdatafilename}' created.")
        #print('step kg 1')
        df_list = [d for _, d in filtered_df.groupby(['Header_image'])]
        #print('step kg 2')
        i=0
        j=0
        for list_split in df_list:
            #print('step kg 3')
            df_list_split = pd.DataFrame(list_split)
            print(df_list_split.shape)
            print(df_list_split)
            G = nx.DiGraph()

            # Iterate through DataFrame rows to add nodes and edges
            for _, row in df_list_split.iterrows():
                #print('step kg 4')
                #print('row[Header_0]',row['Header_0'])
                if 'Header_0' in row:
                    parent = row['Header_0']
                else:
                    parent = row['Text']  # Use 'Text' column if 'Header_0' doesn't exist
                #parent_Header_image = row['Header_image']
                #print('step kg 5')
                parent_Header_image = ''.join(e for e in row['Header_image'] if e.isalnum())+'.png'
                print('parent_Header_image step 1',parent_Header_image)
                if parent_Header_image ==".png":
                    print("Warning: Filtered Header_image is empty. Using default name.")
                    parent_Header_image = row['Text']+"_"+str(i)+"_"+str(j)+'.png'
                #print('step kg 6')
                for child in row[1:]:
                    #print('step kg 7')
                    if pd.notnull(child) and parent != child:  # Check if the child is not null
                        #print('step kg 8')
                        G.add_edge(parent, child)
                        #print(parent,",", child)
                        parent = child
                    #print('step kg 7 for test')
                j=j+1
                #print('step kg 6 for test complete')
            i=i+1
            #print('step kg 2 for test complete')

            # Manually modify node names to avoid ":" characters
            modified_node_names = {node: node.replace(':', '') for node in G.nodes()}
            #knowledgedbgraph.append(parent_Header_image)
            #print('step kg 2B')

            nx.relabel_nodes(G, modified_node_names, copy=False)

            # Convert networkx graph to pydot
            dot_graph = nx.drawing.nx_pydot.to_pydot(G)
            #print('step kg 2C')
            # Render the DOT representation
            dot_graph.set_rankdir('LR')  # Set direction left to right
            #print('step kg 2D')
            dot_graph.set_node_defaults(shape='box', style='filled', fillcolor='lightblue')
            #print('step kg 2E')
            print('parent_Header_image',parent_Header_image)
            print('self.kgdatafilename',self.kgdatafilename)
            #dot_graph.write_png(os.path.join(self.kgdatafilename, parent_Header_image))
            try:
                dot_graph.write_png(os.path.join(self.kgdatafilename, parent_Header_image))
            except Exception as e:
                # Log the exception or print an error message
                print(f"An error occurred while writing the PNG file: {e}")
                # Optionally, you can log the error to a file or handle it differently
            #print('step kg 2F')
        #return knowledgedbgraph




    