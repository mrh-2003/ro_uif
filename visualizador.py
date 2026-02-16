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
    def crear_barras_horizontales(df, x_col, y_col, title, x_label, y_label, color_map=None, log_scale=False):
        if isinstance(df, pd.Series):
            df = df.reset_index()
            if len(df.columns) == 2:
                x_col = df.columns[0]
                y_col = df.columns[1]
        
        # Asegurar que la columna categórica sea string para evitar interpretación numérica
        df[x_col] = df[x_col].astype(str)
        
        fig = px.bar(
            df.head(20),
            x=y_col,
            y=x_col,
            title=title,
            labels={x_col: x_label, y_col: y_label},
            color=y_col,
            color_continuous_scale='Viridis',
            orientation='h',
            log_x=log_scale
        )
        
        fig.update_layout(
            yaxis={'categoryorder':'total ascending', 'type': 'category'},
            height=500,
            hovermode='y unified',
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
        fig.update_layout(
            height=700,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
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
        G = nx.DiGraph()
        
        # Diccionario para guardar atributos de nodos (actividades)
        node_attrs = {}
        
        for _, row in df_relaciones.iterrows():
            origen = str(row[nodo_origen])[:20]
            destino = str(row[nodo_destino])[:20]
            
            # Capturar actividades si existen
            act_origen = str(row.get('actividad_origen', ''))
            act_destino = str(row.get('actividad_destino', ''))
            
            if origen not in node_attrs and act_origen:
                node_attrs[origen] = act_origen
            if destino not in node_attrs and act_destino:
                node_attrs[destino] = act_destino
            
            if peso and peso in row:
                w = float(row[peso])
            else:
                w = 1
            
            # Agregar arista dirigida con etiqueta de monto visible en la línea
            G.add_edge(origen, destino, weight=w, title=f"Monto: {w:,.2f}", label=f"{w:,.0f}")
        
        net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white', directed=True)
        net.from_nx(G)
        
        # Configurar nodos
        for node in net.nodes:
            node_id = node['id']
            # Grado de entrada y salida
            in_degree = G.in_degree(node_id)
            out_degree = G.out_degree(node_id)
            total_degree = in_degree + out_degree
            
            # Actividad
            actividad = node_attrs.get(node_id, 'Sin actividad registrada')
            
            # Tamaño basado en grado total
            node['size'] = total_degree * 5 + 10
            
            # Tooltip con HTML (title)
            tooltip = (
                f"<b>Nodo:</b> {node_id}<br>"
                f"<b>Actividad:</b> {actividad}<br>"
                f"<b>Ingresos:</b> {in_degree} conex.<br>"
                f"<b>Salidas:</b> {out_degree} conex."
            )
            node['title'] = tooltip
            # Guardamos la actividad en el nodo para el JS
            node['actividad'] = actividad
            
            node['color'] = {
                'border': '#2B7CE9',
                'background': '#97C2FC',
                'highlight': {'border': '#2B7CE9', 'background': '#D2E5FF'}
            }
        
        # Configurar aristas (flechas)
        for edge in net.edges:
            edge['arrows'] = 'to'
            edge['width'] = edge.get('weight', 1) / 1000
            if edge['width'] < 1: edge['width'] = 1
            # Configuración de fuente para la etiqueta de la arista
            edge['font'] = {'align': 'middle', 'size': 10, 'color': '#adff2f', 'strokeWidth': 0}
        
        # Configuración de física y opciones para mayor separación
        options = '''
        {
          "physics": {
            "barnesHut": {
              "gravitationalConstant": -80000,
              "centralGravity": 0.1,
              "springLength": 250,
              "springConstant": 0.01,
              "damping": 0.09,
              "avoidOverlap": 1
            },
            "maxVelocity": 40,
            "minVelocity": 0.1,
            "solver": "barnesHut",
            "stabilization": {
              "enabled": true,
              "iterations": 1000
            }
          },
          "nodes": {
            "font": {"size": 14, "color": "white"}
          },
          "edges": {
            "smooth": {
              "type": "cubicBezier",
              "forceDirection": "vertical",
              "roundness": 0.4
            },
            "color": {"inherit": "from"}
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        '''
        net.set_options(options)
        
        # Inyectar JavaScript para manejar el clic y mostrar tabla flotante
        net.save_graph('temp_graph_base.html')
        
        with open('temp_graph_base.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Script JS personalizado para el panel de detalles con scroll general
        custom_js = """
        <style>
            #node-details-panel {
                position: absolute;
                bottom: 20px;
                left: 20px;
                width: 400px;
                max-height: 500px;
                background-color: rgba(0, 0, 0, 0.9);
                color: white;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 15px;
                display: none;
                overflow-y: auto;
                font-family: Arial, sans-serif;
                font-size: 12px;
                z-index: 1000;
                box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            }
            #node-details-panel h3 {
                margin-top: 0;
                border-bottom: 1px solid #666;
                padding-bottom: 8px;
                color: #4da6ff;
                font-size: 16px;
            }
            .detail-section { margin-bottom: 20px; }
            .detail-title { 
                font-weight: bold; 
                color: #aaa; 
                margin-bottom: 8px; 
                text-transform: uppercase; 
                letter-spacing: 0.5px; 
                font-size: 11px;
                border-bottom: 1px solid #333;
                padding-bottom: 2px;
            }
            
            /* Contenedor de lista: Scroll vertical y horizontal GENERAL */
            .list-container {
                max-height: 200px;
                overflow: auto; /* Scroll en ambos ejes si es necesario */
                border: 1px solid #333;
                background: rgba(255,255,255,0.05);
                border-radius: 4px;
                white-space: nowrap; /* Fuerza una sola línea para el contenido ancho */
            }
            
            /* Filas: Display block para listado, sin scroll individual */
            .detail-row { 
                padding: 6px 8px;
                border-bottom: 1px solid #333;
                display: block;
            }
            
            .detail-row:last-child { border-bottom: none; }
            .detail-row:hover { background-color: rgba(255,255,255,0.1); }
            
            /* Scrollbar styling */
            ::-webkit-scrollbar { width: 8px; height: 8px; }
            ::-webkit-scrollbar-track { background: #222; }
            ::-webkit-scrollbar-thumb { background: #555; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #777; }
        </style>
        
        <div id="node-details-panel">
            <h3 id="panel-title">Detalles del Nodo</h3>
            <div id="panel-content">Seleccione un nodo para ver detalles.</div>
        </div>

        <script type="text/javascript">
            network.on("click", function (params) {
                var panel = document.getElementById('node-details-panel');
                
                if (params.nodes.length > 0) {
                    var nodeId = params.nodes[0];
                    var nodeData = nodes.get(nodeId);
                    
                    // Obtener conexiones
                    var connectedEdges = network.getConnectedEdges(nodeId);
                    var edgesData = edges.get(connectedEdges);
                    
                    var ingresos = [];
                    var salidas = [];
                    
                    edgesData.forEach(function(edge) {
                        if (edge.to === nodeId) {
                            var fromNode = nodes.get(edge.from);
                            // Usamos el id, la actividad y el titulo (que contiene el monto formateado largo)
                            ingresos.push({id: edge.from, act: fromNode.actividad || 'Sin info', monto: edge.title});
                        } else if (edge.from === nodeId) {
                            var toNode = nodes.get(edge.to);
                            salidas.push({id: edge.to, act: toNode.actividad || 'Sin info', monto: edge.title});
                        }
                    });
                    
                    var html = "<div class='detail-section'><span class='detail-title'>Actividad:</span> " + (nodeData.actividad || "N/A") + "</div>";
                    
                    html += "<div class='detail-section'><div class='detail-title'>INGRESOS (" + ingresos.length + ")</div><div class='list-container'>";
                    if (ingresos.length > 0) {
                        ingresos.forEach(function(item) {
                            html += "<div class='detail-row'><span>" + item.id + "</span> <span style='color:#ccc'>| " + item.act + "</span> <span style='color:#4da6ff; font-weight:bold'>| " + item.monto + "</span></div>";
                        });
                    } else { html += "<div class='detail-row'><i>Ninguno</i></div>"; }
                    html += "</div></div>";
                    
                    html += "<div class='detail-section'><div class='detail-title'>SALIDAS (" + salidas.length + ")</div><div class='list-container'>";
                    if (salidas.length > 0) {
                        salidas.forEach(function(item) {
                            html += "<div class='detail-row'><span>" + item.id + "</span> <span style='color:#ccc'>| " + item.act + "</span> <span style='color:#4da6ff; font-weight:bold'>| " + item.monto + "</span></div>";
                        });
                    } else { html += "<div class='detail-row'><i>Ninguno</i></div>"; }
                    html += "</div></div>";
                    
                    document.getElementById('panel-title').innerText = nodeId;
                    document.getElementById('panel-content').innerHTML = html;
                    panel.style.display = 'block';
                } else {
                    panel.style.display = 'none';
                }
            });
        </script>
        """
        
        # Inyectar antes del cierre de body
        final_html = html_content.replace('</body>', f'{custom_js}</body>')
        
        # Guardar archivo final
        with open('temp_graph.html', 'w', encoding='utf-8') as f:
            f.write(final_html)
            
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
