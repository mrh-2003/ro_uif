import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from pyvis.network import Network
import pandas as pd

class Visualizador:
    @staticmethod
    def crear_barras(df, x_col, y_col, title, x_label, y_label, color_map=None):
        if isinstance(df, pd.Series):
            df = df.reset_index()
            if len(df.columns) == 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
        
        fig = px.bar(
            df.head(20),
            x=x_col,
            y=y_col,
            title=title,
            labels={x_col: x_label, y_col: y_label},
            color=y_col,
            color_continuous_scale='Viridis'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            hovermode='x unified',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def crear_pie(df, values_col, names_col, title):
        if isinstance(df, pd.Series):
            df = df.reset_index()
            if len(df.columns) == 2:
                names_col = df.columns[0]
                values_col = df.columns[1]
        
        fig = px.pie(
            df.head(10),
            values=values_col,
            names=names_col,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=500)
        
        return fig
    
    @staticmethod
    def crear_barras_agrupadas(df, x_col, y_cols, title, x_label, y_label):
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set2
        
        for i, y_col in enumerate(y_cols):
            fig.add_trace(go.Bar(
                name=y_col,
                x=df[x_col],
                y=df[y_col],
                marker_color=colors[i % len(colors)]
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            barmode='group',
            height=500,
            xaxis_tickangle=-45,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def crear_lineas_tiempo(df, x_col, y_col, title, group_col=None):
        if group_col:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                color=group_col,
                title=title,
                markers=True
            )
        else:
            fig = px.line(
                df,
                x=x_col,
                y=y_col,
                title=title,
                markers=True
            )
        
        fig.update_layout(
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def crear_heatmap(df, title):
        fig = px.imshow(
            df,
            title=title,
            color_continuous_scale='RdYlGn',
            aspect='auto'
        )
        
        fig.update_layout(height=600)
        
        return fig
    
    @staticmethod
    def crear_sunburst(df, path_cols, values_col, title):
        fig = px.sunburst(
            df,
            path=path_cols,
            values=values_col,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(height=600)
        
        return fig
    
    @staticmethod
    def crear_grafo_red(df_relaciones, nodo_origen, nodo_destino, peso=None, titulo="Red de Relaciones"):
        G = nx.Graph()
        
        for _, row in df_relaciones.iterrows():
            origen = str(row[nodo_origen])[:20]
            destino = str(row[nodo_destino])[:20]
            
            if peso and peso in row:
                w = float(row[peso])
            else:
                w = 1
            
            G.add_edge(origen, destino, weight=w)
        
        net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white')
        net.from_nx(G)
        
        for node in net.nodes:
            node['size'] = G.degree[node['id']] * 5 + 10
            node['title'] = f"Nodo: {node['id']}<br>Conexiones: {G.degree[node['id']]}"
            node['color'] = {
                'border': '#2B7CE9',
                'background': '#97C2FC',
                'highlight': {'border': '#2B7CE9', 'background': '#D2E5FF'}
            }
        
        for edge in net.edges:
            edge['title'] = f"Peso: {edge.get('weight', 1)}"
            edge['width'] = edge.get('weight', 1) / 1000
        
        net.set_options('''
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 200,
              "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
          },
          "nodes": {
            "font": {"size": 14}
          },
          "edges": {
            "smooth": {
              "type": "continuous"
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        ''')
        
        return net
    
    @staticmethod
    def crear_scatter(df, x_col, y_col, title, size_col=None, color_col=None):
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            size=size_col,
            color=color_col,
            title=title,
            hover_data=df.columns
        )
        
        fig.update_layout(height=500)
        
        return fig
    
    @staticmethod
    def crear_treemap(df, path_cols, values_col, title):
        fig = px.treemap(
            df,
            path=path_cols,
            values=values_col,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(height=600)
        
        return fig
