import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import base64
from db_manager import DatabaseManager
from analizador import AnalizadorUIF
from visualizador import Visualizador
from generador_informe import GeneradorInforme
import plotly.graph_objects as go
import streamlit.components.v1 as components

st.set_page_config(page_title="Sistema Análisis", layout="wide", page_icon="🔍")

# Fix: Forzar recarga si la instancia en sesión no tiene el método nuevo (get_todas_operaciones)
if 'db_manager' not in st.session_state or not hasattr(st.session_state.db_manager, 'get_todas_operaciones'):
    st.session_state.db_manager = DatabaseManager()

def aplicar_filtros_generales():
    with st.sidebar:
        st.header("🔍 Filtros Generales")
        
        filtros = {}
        
        moneda = st.selectbox("Moneda", ["AMBAS", "SOL", "DOLAR"])
        if moneda != "AMBAS":
            filtros['moneda'] = moneda
        
        tipo_doc = st.selectbox("Tipo Documento", ["AMBOS", "DNI", "RUC"])
        if tipo_doc != "AMBOS":
            filtros['tipo_doc'] = tipo_doc
        
        col1, col2 = st.columns(2)
        with col1:
            monto_min = st.number_input("Monto Mínimo", min_value=0.0, value=0.0)
            if monto_min > 0:
                filtros['monto_min'] = monto_min
        
        with col2:
            monto_max = st.number_input("Monto Máximo", min_value=0.0, value=100000000.0)
            if monto_max > 0:
                filtros['monto_max'] = monto_max
        fecha_inicio_default = date(2016, 1, 1)

        fecha_min = st.sidebar.date_input(
            "Fecha Mínima",
            value=fecha_inicio_default
        ) 
        #fecha_min = st.date_input("Fecha Mínima")
        if fecha_min:
            filtros['fecha_min'] = fecha_min
        
        fecha_max = st.date_input("Fecha Máxima")
        if fecha_max:
            filtros['fecha_max'] = fecha_max
        
        st.subheader("Filtros Adicionales")
        
        df_temp = st.session_state.db_manager.get_todas_operaciones()
        
        if not df_temp.empty:
            if 'flgtipoclibusqueda' in df_temp.columns:
                valores_tipo = df_temp['flgtipoclibusqueda'].dropna().unique().tolist()
                if valores_tipo:
                    tipo_cli = st.multiselect("Tipo Cliente Búsqueda", valores_tipo)
                    if tipo_cli:
                        filtros['flgtipoclibusqueda'] = tipo_cli
            
            if 'destipclasifpartyrelacionado' in df_temp.columns:
                valores_relacion = df_temp['destipclasifpartyrelacionado'].dropna().unique().tolist()
                if valores_relacion:
                    relacion = st.multiselect("Tipo Relación", valores_relacion)
                    if relacion:
                        filtros['destipclasifpartyrelacionado'] = relacion
            
            if 'nbrmonedadestino' in df_temp.columns:
                valores_moneda = df_temp['nbrmonedadestino'].dropna().unique().tolist()
                if valores_moneda:
                    monedas = st.multiselect("Moneda Destino", valores_moneda)
                    if monedas:
                        filtros['nbrmonedadestino'] = monedas
            
            if 'descanal' in df_temp.columns:
                valores_canal = df_temp['descanal'].dropna().unique().tolist()
                if valores_canal:
                    canales = st.multiselect("Canal", valores_canal)
                    if canales:
                        filtros['descanal'] = canales
            
            if 'SEGMENTO' in df_temp.columns:
                valores_segmento = df_temp['SEGMENTO'].dropna().unique().tolist()
                if valores_segmento:
                    segmentos = st.multiselect("Segmento", valores_segmento)
                    if segmentos:
                        filtros['segmento'] = segmentos
            
            if 'destipopereportesbs' in df_temp.columns:
                valores_operacion = df_temp['destipopereportesbs'].dropna().unique().tolist()
                if valores_operacion:
                    operaciones = st.multiselect("Tipo Operación", valores_operacion)
                    if operaciones:
                        filtros['destipopereportesbs'] = operaciones
            
            efectivo = st.checkbox("Solo operaciones en efectivo")
            if efectivo:
                filtros['efectivo_only'] = True
        
        return filtros

def descargar_excel(df, nombre_archivo):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=True, sheet_name='Datos')
    
    output.seek(0)
    b64 = base64.b64encode(output.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{nombre_archivo}">📥 Descargar Excel</a>'
    st.markdown(href, unsafe_allow_html=True)

def pagina_carga_datos():
    st.title("📤 Carga de Datos")
    
    codigo_carga = st.text_input("Código de Carga (identificador único)", key="codigo_carga")
    
    archivo = st.file_uploader("Seleccionar archivo Excel", type=['xlsx', 'xls'])
    
    if archivo and codigo_carga:
        if st.button("Cargar Datos", type="primary"):
            try:
                df = pd.read_excel(archivo)
                
                st.write("Vista previa de los datos:")
                st.dataframe(df.head())
                
                columnas_requeridas = [
                    'CODUNICOCLI_13_enc', 'fec_operacion', 'mtotrx'
                ]
                
                columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
                if columnas_faltantes:
                    st.error(f"Faltan las columnas: {', '.join(columnas_faltantes)}")
                    return
                
                if 'fec_operacion' in df.columns:
                    df['fec_operacion'] = pd.to_datetime(df['fec_operacion'], errors='coerce')
                
                if 'mtotrx' in df.columns:
                    df['mtotrx'] = pd.to_numeric(df['mtotrx'], errors='coerce')
                
                exito, resultado = st.session_state.db_manager.cargar_datos(
                    df, codigo_carga, archivo.name
                )
                
                if exito:
                    st.success(f"✅ Datos cargados exitosamente. ID de carga: {resultado}")
                    st.balloons()
                else:
                    st.error(f"❌ Error al cargar datos: {resultado}")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    st.subheader("Cargas Existentes")
    
    df_cargas = st.session_state.db_manager.get_cargas()
    if not df_cargas.empty:
        st.dataframe(df_cargas, use_container_width=True)
    else:
        st.info("No hay cargas registradas")

def pagina_gestion_casos():
    st.title("📁 Gestión de Casos")
    st.info("ℹ️ El análisis ahora se realiza sobre toda la base de datos, pero puedes seguir agrupando casos para referencia.")
    
    tab1, tab2, tab3 = st.tabs(["Crear Caso", "Ver Casos", "Eliminar Caso"])
    
    with tab1:
        st.subheader("Crear Nuevo Caso")
        
        nombre_caso = st.text_input("Nombre del Caso")
        descripcion_caso = st.text_area("Descripción")
        
        metodo = st.radio("Método de Selección", ["Por Clientes", "Por Código de Carga"])
        
        df_cargas = st.session_state.db_manager.get_cargas()

        if metodo == "Por Clientes":
            if not df_cargas.empty:
                carga_sel = st.selectbox("Seleccionar Carga", df_cargas['codigo_carga'].astype(str).tolist(), key="sel_carga_cli")
                
                if carga_sel:
                    id_carga = df_cargas[df_cargas['codigo_carga'].astype(str) == carga_sel]['id_carga'].values[0]
                    
                    df_ops = pd.read_sql(
                        f"SELECT DISTINCT CODUNICOCLI_13_enc FROM operaciones WHERE id_carga = {id_carga}",
                        st.session_state.db_manager.get_connection()
                    )
                    
                    clientes_disponibles = df_ops['CODUNICOCLI_13_enc'].tolist()
                    clientes_seleccionados = st.multiselect("Seleccionar Clientes", clientes_disponibles)
                    
                    if st.button("Crear Caso con Clientes Seleccionados"):
                        if nombre_caso and clientes_seleccionados:
                            exito, id_caso = st.session_state.db_manager.crear_caso(nombre_caso, descripcion_caso)
                            if exito:
                                st.session_state.db_manager.agregar_clientes_a_caso(id_caso, clientes_seleccionados)
                                st.success(f"✅ Caso creado exitosamente. ID: {id_caso}")
                        else:
                            st.warning("Ingrese nombre y seleccione clientes")
            else:
                st.warning("No hay cargas disponibles")
        
        else:
            if not df_cargas.empty:
                cargas_seleccionadas = st.multiselect(
                    "Seleccionar Cargas",
                    df_cargas['codigo_carga'].astype(str).tolist(),
                    key="sel_carga_multi"
                )
                
                if st.button("Crear Caso con Cargas Seleccionadas"):
                    if nombre_caso and cargas_seleccionadas:
                        exito, id_caso = st.session_state.db_manager.crear_caso(nombre_caso, descripcion_caso)
                        if exito:
                            for carga in cargas_seleccionadas:
                                id_carga = df_cargas[df_cargas['codigo_carga'].astype(str) == carga]['id_carga'].values[0]
                                st.session_state.db_manager.agregar_carga_a_caso(id_caso, id_carga)
                            st.success(f"✅ Caso creado exitosamente. ID: {id_caso}")
                    else:
                        st.warning("Ingrese nombre y seleccione cargas")
            else:
                st.warning("No hay cargas disponibles")
    
    with tab2:
        st.subheader("Casos Existentes")
        df_casos = st.session_state.db_manager.get_casos()
        
        if not df_casos.empty:
            st.dataframe(df_casos, use_container_width=True)
        else:
            st.info("No hay casos registrados")
    
    with tab3:
        st.subheader("Eliminar Caso")
        df_casos = st.session_state.db_manager.get_casos()
        
        if not df_casos.empty:
            caso_eliminar = st.selectbox("Seleccionar Caso a Eliminar", df_casos['nombre_caso'].tolist())
            
            if caso_eliminar:
                id_caso = df_casos[df_casos['nombre_caso'] == caso_eliminar]['id_caso'].values[0]
                
                if st.button("Eliminar Caso", type="primary"):
                    if st.session_state.db_manager.eliminar_caso(id_caso):
                        st.success("✅ Caso eliminado exitosamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar caso")
        else:
            st.info("No hay casos para eliminar")

def pagina_analisis():
    st.title("📊 Análisis General")
    st.markdown("Analizando **toda la base de datos** disponible.")
    
    filtros = aplicar_filtros_generales()
    
    df_operaciones = st.session_state.db_manager.get_todas_operaciones(filtros)
    
    if df_operaciones.empty:
        st.warning("No hay operaciones registradas o no coinciden con los filtros aplicados.")
        return
    
    st.success(f"Total de operaciones analizadas: {len(df_operaciones):,}")
    
    analizador = AnalizadorUIF(df_operaciones)
    viz = Visualizador()
    
    st.subheader("Seleccione el Tipo de Análisis")
    
    categorias = {
        "📈 Reportes Generales": [
            "Top 10 por Columnas",
            "Ranking de Operaciones",
            "Ranking de Agencias",
            "Minería en Origen de Fondos"
        ],
        "👥 Análisis de Actores": [
            "Ejecutantes Comunes",
            "Ordenantes Comunes",
            "Beneficiarios Comunes",
            "Ranking de Ejecutantes",
            "Ranking de Ordenantes",
            "Ranking de Beneficiarios"
        ],
        "💰 Análisis de Operaciones": [
            "Post Transferencia Internacional",
            "Operaciones Simultáneas",
            "Porcentaje de Efectivo",
            "Cuentas Ordenantes Comunes",
            "Cuentas Beneficiarias Comunes"
        ],
        "🎯 Análisis de Actividades": [
            "Actividad Económica - Ejecutantes",
            "Actividad Económica - Ordenantes",
            "Actividad Económica - Beneficiarios",
            "Actividades de Riesgo"
        ]
    }
    
    categoria_sel = st.selectbox("Categoría", list(categorias.keys()))
    analisis_sel = st.selectbox("Análisis", categorias[categoria_sel])
    
    # Inicializar estado si no existe
    if 'analisis_activo' not in st.session_state:
        st.session_state.analisis_activo = False
        
    # Detectar cambio en la selección para resetear
    if 'last_analisis' not in st.session_state:
        st.session_state.last_analisis = analisis_sel
    
    if st.session_state.last_analisis != analisis_sel:
        st.session_state.analisis_activo = False
        st.session_state.last_analisis = analisis_sel

    if st.button("🚀 Ejecutar Análisis", type="primary"):
        st.session_state.analisis_activo = True
        
    if st.session_state.analisis_activo:
        ejecutar_analisis(analisis_sel, analizador, viz, df_operaciones)

def ejecutar_analisis(tipo_analisis, analizador, viz, df_operaciones):
    st.divider()
    
    if tipo_analisis == "Top 10 por Columnas":
        st.header("📊 Top 10 por Columnas Relevantes")
        resultados = analizador.reporte_top10_columnas()
        
        for nombre, df in resultados.items():
            st.subheader(f"Top 10 - {nombre.replace('_', ' ').title()}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(df, use_container_width=True)
                descargar_excel(df, f"top10_{nombre}.xlsx")
            
            with col2:
                if not df.empty:
                    log_scale = st.checkbox("Escala Logarítmica", value=False, key=f"log_{nombre}")
                    fig = viz.crear_barras_horizontales(
                        df.reset_index(),
                        df.index.name if df.index.name else 'index',
                        'cantidad',
                        f'Top 10 - {nombre}',
                        nombre,
                        'Cantidad',
                        log_scale=log_scale
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
    
    elif tipo_analisis == "Post Transferencia Internacional":
        st.header("🌍 Análisis Post Transferencia Internacional")
        
        dias_seguimiento = st.slider("Días de Seguimiento Posterior", min_value=1, max_value=30, value=7)
        
        ranking, stats, casos = analizador.reporte_2_ranking_post_transferencia_internacional(dias_seguimiento)
        
        if not ranking.empty:
            # Gráfico Pie Grande Arriba
            fig = viz.crear_pie(
                ranking.reset_index(),
                'cantidad_operaciones',
                'operacion_siguiente',
                'Operaciones Posteriores a Transferencias Internacionales'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.divider()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Resumen")
                st.metric("Total Recepciones Internacionales", f"{stats['total_recepciones']:,}")
                st.metric("Con Salidas Posteriores", f"{stats['total_con_salidas']:,}")
                st.metric("Porcentaje", f"{stats['porcentaje']:.2f}%")
            
            with col2:
                st.subheader("Ranking de Tipos de Operación Siguiente")
                st.dataframe(ranking, use_container_width=True)
                descargar_excel(ranking, "ranking_primeras_operaciones.xlsx")

            st.divider()
            st.subheader("📋 Detalle de Movimientos por Transferencia")
            st.info(f"Mostrando salidas detectadas hasta la siguiente transferencia internacional o hasta {dias_seguimiento} días después.")
            
            if casos:
                for i, caso in enumerate(casos):
                    monto_entrada = caso['entrada'].get('mtotrx', 0)
                    moneda = caso['entrada'].get('nbrmonedadestino', 'N/A')
                    cliente = caso['entrada'].get('CODUNICOCLI_13_enc', 'Desconocido')
                    fec = pd.to_datetime(caso['entrada'].get('fec_operacion')).strftime('%Y-%m-%d')
                    
                    titulo = f"Caso #{i+1} | Cliente: {cliente} | Fecha: {fec} | Monto: {monto_entrada:,.2f} {moneda}"
                    
                    with st.expander(titulo, expanded=False):
                        col_a, col_b = st.columns([1, 2])
                        
                        with col_a:
                            st.markdown("#### 📥 Entrada (Origen)")
                            campos_clave = [
                                'fec_operacion', 'hora_operacion', 'mtotrx', 'nbrmonedadestino', 
                                'destipopereportesbs', 'codigo_ubigeo', 'descanal'
                            ]
                            entrada_data = caso['entrada']
                            entrada_filtrada = {k: entrada_data[k] for k in campos_clave if k in entrada_data.index}
                            st.table(pd.DataFrame([entrada_filtrada]).T.rename(columns={0: 'Valor'}))

                        with col_b:
                            st.markdown("#### 📤 Salidas Detectadas")
                            df_salidas = caso['salidas']
                            st.dataframe(df_salidas, use_container_width=True)
                            descargar_excel(df_salidas, f"salidas_caso_{i+1}.xlsx")
            else:
                st.warning("No se encontraron casos con salidas posteriores relevantes en la ventana de tiempo analizada.")

        else:
            st.info("No se encontraron transferencias internacionales o operaciones posteriores")

    elif tipo_analisis == "Ejecutantes Comunes":
        st.header("👤 Ejecutantes Comunes entre Clientes")
        resultado = analizador.reporte_3_ejecutantes_comunes()
        
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True)
            descargar_excel(resultado, "ejecutantes_comunes.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_ejecutantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = viz.crear_barras_horizontales(
                    resultado.head(20).reset_index(),
                    'doc_ejecutante_encriptado',
                    'cantidad_clientes',
                    'Top 20 Ejecutantes por Cantidad de Clientes',
                    'Ejecutante',
                    'Cantidad de Clientes',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = viz.crear_barras_horizontales(
                    resultado.head(20).reset_index(),
                    'doc_ejecutante_encriptado',
                    'monto_total',
                    'Top 20 Ejecutantes por Monto Total',
                    'Ejecutante',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if len(resultado) > 0:
                st.subheader("Red de Relaciones - Ejecutantes")
                df_red = []
                for idx, row in resultado.head(50).iterrows():
                    for cliente in row['clientes_diferentes']:
                        df_red.append({
                            'ejecutante': idx[:20],
                            'cliente': cliente[:20],
                            'monto': row['monto_total'],
                            'actividad_origen': row.get('actividad', ''), # Actividad ejecutante (nombre col rename en analizador)
                            'actividad_destino': 'Cliente' 
                        })
                
                if df_red:
                    df_red = pd.DataFrame(df_red)
                    net = viz.crear_grafo_red(df_red, 'ejecutante', 'cliente', 'monto')
                    # PyVis generates file, we read it
                    # Note: crear_grafo_red now handles JavaScript injection internally and saves to temp_graph.html
                    # We just need to read it back.
                    with open('temp_graph.html', 'r', encoding='utf-8') as f:
                        html_string = f.read()
                    components.html(html_string, height=800)
        else:
            st.info("No se encontraron ejecutantes comunes")
    
    elif tipo_analisis == "Ordenantes Comunes":
        st.header("💼 Ordenantes Comunes entre Clientes")
        resultado = analizador.reporte_4_ordenantes_comunes()
        
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True)
            descargar_excel(resultado, "ordenantes_comunes.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_ordenantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = viz.crear_barras_horizontales(
                    resultado.head(20).reset_index(),
                    'doc_ordenante_encriptado',
                    'cantidad_clientes',
                    'Top 20 Ordenantes por Cantidad de Clientes',
                    'Ordenante',
                    'Cantidad de Clientes',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = viz.crear_barras_horizontales(
                    resultado.head(20).reset_index(),
                    'doc_ordenante_encriptado',
                    'monto_total',
                    'Top 20 Ordenantes por Monto Total',
                    'Ordenante',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if len(resultado) > 0:
                st.subheader("Red de Relaciones - Ordenantes")
                df_red = []
                for idx, row in resultado.head(50).iterrows():
                    for cliente in row['clientes_diferentes']:
                        df_red.append({
                            'ordenante': idx[:20],
                            'cliente': cliente[:20],
                            'monto': row['monto_total'],
                            'actividad_origen': row.get('actividad', ''), # Actividad ordenante (nombre col rename en analizador)
                            'actividad_destino': 'Cliente'
                        })
                
                if df_red:
                    df_red = pd.DataFrame(df_red)
                    net = viz.crear_grafo_red(df_red, 'ordenante', 'cliente', 'monto')
                    with open('temp_graph.html', 'r', encoding='utf-8') as f:
                        html_string = f.read()
                    components.html(html_string, height=800)
        else:
            st.info("No se encontraron ordenantes comunes")
    
    elif tipo_analisis == "Beneficiarios Comunes":
        st.header("🎯 Beneficiarios Comunes entre Clientes")
        resultado = analizador.reporte_5_beneficiarios_comunes()
        
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True)
            descargar_excel(resultado, "beneficiarios_comunes.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_beneficiarios")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = viz.crear_barras_horizontales(
                    resultado.head(20).reset_index(),
                    'doc_beneficiario_encriptado',
                    'cantidad_clientes',
                    'Top 20 Beneficiarios por Cantidad de Clientes',
                    'Beneficiario',
                    'Cantidad de Clientes',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = viz.crear_barras_horizontales(
                    resultado.head(20).reset_index(),
                    'doc_beneficiario_encriptado',
                    'monto_total',
                    'Top 20 Beneficiarios por Monto Total',
                    'Beneficiario',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            if len(resultado) > 0:
                st.subheader("Red de Relaciones - Beneficiarios")
                df_red = []
                for idx, row in resultado.head(50).iterrows():
                    for cliente in row['clientes_diferentes']:
                        df_red.append({
                            'beneficiario': idx[:20],
                            'cliente': cliente[:20],
                            'monto': row['monto_total'],
                            'actividad_origen': row.get('actividad', ''), # Actividad beneficiario (nombre col rename en analizador)
                            'actividad_destino': 'Cliente'
                        })
                
                if df_red:
                    df_red = pd.DataFrame(df_red)
                    net = viz.crear_grafo_red(df_red, 'beneficiario', 'cliente', 'monto')
                    with open('temp_graph.html', 'r', encoding='utf-8') as f:
                        html_string = f.read()
                    components.html(html_string, height=800)
        else:
            st.info("No se encontraron beneficiarios comunes")
    
    elif tipo_analisis == "Ranking de Ejecutantes":
        st.header("🏆 Ranking de Ejecutantes")
        ranking = analizador.reporte_6_ranking_ejecutantes()
        
        if not ranking.empty:
            st.dataframe(ranking, use_container_width=True)
            descargar_excel(ranking, "ranking_ejecutantes.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_rank_ejecutantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                top = ranking.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'doc_ejecutante_encriptado',
                    'num_operaciones',
                    'Top 15 Ejecutantes por Número de Operaciones',
                    'Ejecutante',
                    'Operaciones',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                top = ranking.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'doc_ejecutante_encriptado',
                    'monto_total',
                    'Top 15 Ejecutantes por Monto',
                    'Ejecutante',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ejecutantes")
    
    elif tipo_analisis == "Ranking de Ordenantes":
        st.header("🏆 Ranking de Ordenantes")
        ranking = analizador.reporte_7_ranking_ordenantes()
        
        if not ranking.empty:
            st.dataframe(ranking, use_container_width=True)
            descargar_excel(ranking, "ranking_ordenantes.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_rank_ordenantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                top = ranking.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'doc_ordenante_encriptado',
                    'num_operaciones',
                    'Top 15 Ordenantes por Número de Operaciones',
                    'Ordenante',
                    'Operaciones',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                top = ranking.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'doc_ordenante_encriptado',
                    'monto_total',
                    'Top 15 Ordenantes por Monto',
                    'Ordenante',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ordenantes")
    
    elif tipo_analisis == "Ranking de Beneficiarios":
        st.header("🏆 Ranking de Beneficiarios")
        ranking = analizador.reporte_8_ranking_beneficiarios()
        
        if not ranking.empty:
            st.dataframe(ranking, use_container_width=True)
            descargar_excel(ranking, "ranking_beneficiarios.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_rank_beneficiarios")
            
            col1, col2 = st.columns(2)
            
            with col1:
                top = ranking.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'doc_beneficiario_encriptado',
                    'num_operaciones',
                    'Top 15 Beneficiarios por Número de Operaciones',
                    'Beneficiario',
                    'Operaciones',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                top = ranking.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'doc_beneficiario_encriptado',
                    'monto_total',
                    'Top 15 Beneficiarios por Monto',
                    'Beneficiario',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de beneficiarios")
    
    elif tipo_analisis == "Porcentaje de Efectivo":
        st.header("💵 Porcentaje de Efectivo por Cliente")
        resultado = analizador.reporte_9_porcentaje_efectivo()
        
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True)
            descargar_excel(resultado, "porcentaje_efectivo.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_efectivo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                top = resultado.head(20).reset_index()
                # Recortar nombre cliente para gráfico
                top['cliente_short'] = top['CODUNICOCLI_13_enc'].astype(str).str[:8]
                
                fig = viz.crear_barras_horizontales(
                    top,
                    'cliente_short',
                    'porcentaje_efectivo',
                    'Top 20 Clientes por % Efectivo (Operaciones)',
                    'Cliente (Init)',
                    '% Efectivo',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                top = resultado.sort_values('porcentaje_monto_efectivo', ascending=False).head(20).reset_index()
                # Recortar nombre cliente para gráfico
                top['cliente_short'] = top['CODUNICOCLI_13_enc'].astype(str).str[:8]
                
                fig = viz.crear_barras_horizontales(
                    top,
                    'cliente_short',
                    'porcentaje_monto_efectivo',
                    'Top 20 Clientes por % Monto en Efectivo',
                    'Cliente (Init)',
                    '% Monto Efectivo',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos disponibles")
    
    elif tipo_analisis == "Cuentas Ordenantes Comunes":
        st.header("🏦 Cuentas Ordenantes Comunes")
        resultado = analizador.reporte_10_cuentas_ordenantes_comunes()
        
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True)
            descargar_excel(resultado, "cuentas_ordenantes_comunes.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_ctas_ordenantes")
            
            col1, col2 = st.columns(2)
            
            with col1:
                top = resultado.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'codcta20ordenante',
                    'cantidad_clientes',
                    'Top 15 Cuentas Ordenantes por Clientes',
                    'Cuenta',
                    'Clientes',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                top = resultado.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'codcta20ordenante',
                    'monto_total',
                    'Top 15 Cuentas Ordenantes por Monto',
                    'Cuenta',
                    'Monto',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontraron cuentas ordenantes comunes")
    
    elif tipo_analisis == "Cuentas Beneficiarias Comunes":
        st.header("🏦 Cuentas Beneficiarias Comunes")
        resultado = analizador.reporte_11_cuentas_beneficiarias_comunes()
        
        if not resultado.empty:
            st.dataframe(resultado, use_container_width=True)
            descargar_excel(resultado, "cuentas_beneficiarias_comunes.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_ctas_beneficiarias")
            
            col1, col2 = st.columns(2)
            
            with col1:
                top = resultado.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'codcta20beneficiario',
                    'cantidad_clientes',
                    'Top 15 Cuentas Beneficiarias por Clientes',
                    'Cuenta',
                    'Clientes',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                top = resultado.head(15).reset_index()
                fig = viz.crear_barras_horizontales(
                    top,
                    'codcta20beneficiario',
                    'monto_total',
                    'Top 15 Cuentas Beneficiarias por Monto',
                    'Cuenta',
                    'Monto',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontraron cuentas beneficiarias comunes")
    
    elif tipo_analisis == "Operaciones Simultáneas":
        st.header("⚡ Operaciones Simultáneas")
        
        col_unit, col_val = st.columns([1, 3])
        
        with col_unit:
            unidad_tiempo = st.selectbox("Unidad de Tiempo", ["Minutos", "Horas", "Días"])
        
        with col_val:
            if unidad_tiempo == "Minutos":
                valor_tiempo = st.slider("Ventana de tiempo (minutos)", 0, 60, 30, key="slider_min")
                minutos_totales = valor_tiempo
            elif unidad_tiempo == "Horas":
                valor_tiempo = st.slider("Ventana de tiempo (horas)", 1, 24, 1, key="slider_hour")
                minutos_totales = valor_tiempo * 60
            else: # Días
                valor_tiempo = st.slider("Ventana de tiempo (días)", 1, 7, 1, key="slider_day")
                minutos_totales = valor_tiempo * 24 * 60
        
        resultado, stats = analizador.reporte_12_operaciones_simultaneas(minutos_totales)
        
        if not resultado.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Casos", f"{stats['total_casos']:,}")
            with col2:
                st.metric("Promedio % Dispuesto", f"{stats['promedio_porcentaje']:.2f}%")
            with col3:
                st.metric("Monto Total Dispuesto", f"${stats['monto_total_dispuesto']:,.2f}")
            
            st.dataframe(resultado, use_container_width=True)
            descargar_excel(resultado, "operaciones_simultaneas.xlsx")
            
            # Corrección aplicada aquí: size_col='cantidad_operaciones_salida'
            fig = viz.crear_scatter(
                resultado,
                'monto_recibido',
                'porcentaje_dispuesto',
                'Relación Monto Recibido vs % Dispuesto',
                size_col='cantidad_operaciones_salida',
                color_col='porcentaje_dispuesto'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No se encontraron operaciones simultáneas")
    
    elif tipo_analisis == "Ranking de Operaciones":
        st.header("📋 Ranking de Tipos de Operaciones")
        ranking_cant, ranking_monto = analizador.reporte_13_ranking_operaciones()
        
        tab1, tab2 = st.tabs(["Por Cantidad", "Por Monto"])
        
        with tab1:
            st.dataframe(ranking_cant, use_container_width=True)
            descargar_excel(ranking_cant, "ranking_operaciones_cantidad.xlsx")
            
            log_scale_cant = st.checkbox("Escala Logarítmica", value=False, key="log_ops_cant")
            fig = viz.crear_barras_horizontales(
                ranking_cant.head(15).reset_index(),
                'destipopereportesbs',
                'cantidad_operaciones',
                'Top 15 Operaciones por Cantidad',
                'Tipo de Operación',
                'Cantidad',
                log_scale=log_scale_cant
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(ranking_monto, use_container_width=True)
            descargar_excel(ranking_monto, "ranking_operaciones_monto.xlsx")
            
            log_scale_monto = st.checkbox("Escala Logarítmica", value=False, key="log_ops_monto")
            fig = viz.crear_barras_horizontales(
                ranking_monto.head(15).reset_index(),
                'destipopereportesbs',
                'monto_total',
                'Top 15 Operaciones por Monto',
                'Tipo de Operación',
                'Monto Total',
                log_scale=log_scale_monto
            )
            st.plotly_chart(fig, use_container_width=True)

    elif tipo_analisis == "Actividad Económica - Ejecutantes":
        st.header("💼 Actividad Económica - Ejecutantes")
        ranking_cant, ranking_monto = analizador.reporte_14_actividad_ejecutantes()
        
        tab1, tab2 = st.tabs(["Por Cantidad", "Por Monto"])
        
        with tab1:
            st.dataframe(ranking_cant, use_container_width=True)
            descargar_excel(ranking_cant, "actividad_ejecutantes_cantidad.xlsx")
            
            log_scale_c = st.checkbox("Escala Logarítmica", value=False, key="log_act_eje_cant")
            fig = viz.crear_barras_horizontales(
                ranking_cant.head(15).reset_index(),
                'DesOcupSOL',
                'cantidad_operaciones',
                'Top 15 Actividades Ejecutantes por Cantidad',
                'Actividad',
                'Cantidad',
                log_scale=log_scale_c
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(ranking_monto, use_container_width=True)
            descargar_excel(ranking_monto, "actividad_ejecutantes_monto.xlsx")
            
            log_scale_m = st.checkbox("Escala Logarítmica", value=False, key="log_act_eje_monto")
            fig = viz.crear_barras_horizontales(
                ranking_monto.head(15).reset_index(),
                'DesOcupSOL',
                'monto_total',
                'Top 15 Actividades Ejecutantes por Monto',
                'Actividad',
                'Monto Total',
                log_scale=log_scale_m
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif tipo_analisis == "Actividad Económica - Ordenantes":
        st.header("💼 Actividad Económica - Ordenantes")
        ranking_cant, ranking_monto = analizador.reporte_15_actividad_ordenantes()
        
        tab1, tab2 = st.tabs(["Por Cantidad", "Por Monto"])
        
        with tab1:
            st.dataframe(ranking_cant, use_container_width=True)
            descargar_excel(ranking_cant, "actividad_ordenantes_cantidad.xlsx")
            
            log_scale_c = st.checkbox("Escala Logarítmica", value=False, key="log_act_ord_cant")
            fig = viz.crear_barras_horizontales(
                ranking_cant.head(15).reset_index(),
                'DesOcupOrd',
                'cantidad_operaciones',
                'Top 15 Actividades Ordenantes por Cantidad',
                'Actividad',
                'Cantidad',
                log_scale=log_scale_c
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(ranking_monto, use_container_width=True)
            descargar_excel(ranking_monto, "actividad_ordenantes_monto.xlsx")
            
            log_scale_m = st.checkbox("Escala Logarítmica", value=False, key="log_act_ord_monto")
            fig = viz.crear_barras_horizontales(
                ranking_monto.head(15).reset_index(),
                'DesOcupOrd',
                'monto_total',
                'Top 15 Actividades Ordenantes por Monto',
                'Actividad',
                'Monto Total',
                log_scale=log_scale_m
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif tipo_analisis == "Actividad Económica - Beneficiarios":
        st.header("💼 Actividad Económica - Beneficiarios")
        ranking_cant, ranking_monto = analizador.reporte_16_actividad_beneficiarios()
        
        tab1, tab2 = st.tabs(["Por Cantidad", "Por Monto"])
        
        with tab1:
            st.dataframe(ranking_cant, use_container_width=True)
            descargar_excel(ranking_cant, "actividad_beneficiarios_cantidad.xlsx")
            
            log_scale_c = st.checkbox("Escala Logarítmica", value=False, key="log_act_ben_cant")
            fig = viz.crear_barras_horizontales(
                ranking_cant.head(15).reset_index(),
                'DesOcupBen',
                'cantidad_operaciones',
                'Top 15 Actividades Beneficiarios por Cantidad',
                'Actividad',
                'Cantidad',
                log_scale=log_scale_c
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.dataframe(ranking_monto, use_container_width=True)
            descargar_excel(ranking_monto, "actividad_beneficiarios_monto.xlsx")
            
            log_scale_m = st.checkbox("Escala Logarítmica", value=False, key="log_act_ben_monto")
            fig = viz.crear_barras_horizontales(
                ranking_monto.head(15).reset_index(),
                'DesOcupBen',
                'monto_total',
                'Top 15 Actividades Beneficiarios por Monto',
                'Actividad',
                'Monto Total',
                log_scale=log_scale_m
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif tipo_analisis == "Actividades de Riesgo":
        st.header("⚠️ Actividades de Riesgo")
        resultados = analizador.reporte_17_actividades_riesgo()
        
        tab1, tab2, tab3 = st.tabs([
            "Bombas/Compresores",
            "Seguridad Privada",
            "Transporte (>10k PEN o >3k USD)"
        ])
        
        with tab1:
            st.subheader("Clientes con Beneficiarios: Bombas/Compresores/Grifos/Válvulas")
            if not resultados['bombas_compresores'].empty:
                st.dataframe(resultados['bombas_compresores'], use_container_width=True)
                descargar_excel(resultados['bombas_compresores'], "riesgo_bombas_compresores.xlsx")
                
                log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_riesgo_bombas")
                fig = viz.crear_barras_horizontales(
                    resultados['bombas_compresores'].head(15).reset_index(),
                    'CODUNICOCLI_13_enc',
                    'monto_total',
                    'Clientes - Bombas/Compresores',
                    'Cliente',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No se encontraron casos")
        
        with tab2:
            st.subheader("Clientes con Beneficiarios: Seguridad Privada")
            if not resultados['seguridad_privada'].empty:
                st.dataframe(resultados['seguridad_privada'], use_container_width=True)
                descargar_excel(resultados['seguridad_privada'], "riesgo_seguridad_privada.xlsx")
                
                log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_riesgo_seguridad")
                fig = viz.crear_barras_horizontales(
                    resultados['seguridad_privada'].head(15).reset_index(),
                    'CODUNICOCLI_13_enc',
                    'monto_total',
                    'Clientes - Seguridad Privada',
                    'Cliente',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No se encontraron casos")
        
        with tab3:
            st.subheader("Clientes con Beneficiarios: Transporte (>10k PEN o >3k USD)")
            if not resultados['transporte'].empty:
                st.dataframe(resultados['transporte'], use_container_width=True)
                descargar_excel(resultados['transporte'], "riesgo_transporte.xlsx")
                
                log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_riesgo_transporte")
                fig = viz.crear_barras_horizontales(
                    resultados['transporte'].head(15).reset_index(),
                    'CODUNICOCLI_13_enc',
                    'monto_total',
                    'Clientes - Transporte',
                    'Cliente',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No se encontraron casos")
    
    elif tipo_analisis == "Ranking de Agencias":
        st.header("🏢 Ranking de Agencias/Ubigeos")
        ranking = analizador.reporte_18_ranking_agencias()
        
        if not ranking.empty:
            ranking = ranking.reset_index()
            ranking['codigo_ubigeo'] = ranking['codigo_ubigeo'].astype(str)
            st.dataframe(ranking, use_container_width=True)
            descargar_excel(ranking, "ranking_agencias.xlsx")
            
            log_scale = st.checkbox("Escala Logarítmica", value=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = viz.crear_barras_horizontales(
                    ranking.head(20),
                    'codigo_ubigeo',
                    'cantidad_operaciones',
                    'Top 20 Agencias por Cantidad',
                    'Ubigeo',
                    'Operaciones',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = viz.crear_barras_horizontales(
                    ranking.head(20),
                    'codigo_ubigeo',
                    'monto_total',
                    'Top 20 Agencias por Monto',
                    'Ubigeo',
                    'Monto Total',
                    log_scale=log_scale
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de agencias")

    elif tipo_analisis == "Minería en Origen de Fondos":
        st.header("⛏️ Actividad Económica - Minería en Origen de Fondos")
        st.markdown("Análisis de operaciones donde el **origen de fondos** menciona 'minera' o 'minería'.")
        
        resultados, total_ops = analizador.reporte_19_actividad_mineria()
        
        st.metric("Total Operaciones Detectadas", f"{total_ops:,}")
        
        if total_ops > 0:
            tab1, tab2, tab3 = st.tabs(["Ejecutantes", "Ordenantes", "Beneficiarios"])
            
            log_scale = st.checkbox("Escala Logarítmica", value=False, key="log_mineria")
            
            with tab1:
                st.subheader("Actividad Económica - Ejecutantes")
                df = resultados.get('ejecutantes', pd.DataFrame())
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    descargar_excel(df, "mineria_ejecutantes.xlsx")
                    
                    fig = viz.crear_barras_horizontales(
                        df.head(15).reset_index(),
                        'DesOcupSOL',
                        'cantidad_operaciones',
                        'Top 15 Actividades (Ejecutantes) en Minería',
                        'Actividad',
                        'Cantidad',
                        log_scale=log_scale
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos de ejecutantes")
            
            with tab2:
                st.subheader("Actividad Económica - Ordenantes")
                df = resultados.get('ordenantes', pd.DataFrame())
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    descargar_excel(df, "mineria_ordenantes.xlsx")
                    
                    fig = viz.crear_barras_horizontales(
                        df.head(15).reset_index(),
                        'DesOcupOrd',
                        'cantidad_operaciones',
                        'Top 15 Actividades (Ordenantes) en Minería',
                        'Actividad',
                        'Cantidad',
                        log_scale=log_scale
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos de ordenantes")
            
            with tab3:
                st.subheader("Actividad Económica - Beneficiarios")
                df = resultados.get('beneficiarios', pd.DataFrame())
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    descargar_excel(df, "mineria_beneficiarios.xlsx")
                    
                    fig = viz.crear_barras_horizontales(
                        df.head(15).reset_index(),
                        'DesOcupBen',
                        'cantidad_operaciones',
                        'Top 15 Actividades (Beneficiarios) en Minería',
                        'Actividad',
                        'Cantidad',
                        log_scale=log_scale
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No hay datos de beneficiarios")
        else:
            st.warning("No se encontraron operaciones relacionadas con minería en el origen de fondos.")

def pagina_informe():
    st.title("📄 Generación de Informe PDF")
    st.markdown("Generando informe sobre **toda la base de datos**.")
    
    filtros = aplicar_filtros_generales()
    
    df_operaciones = st.session_state.db_manager.get_todas_operaciones(filtros)
    
    if df_operaciones.empty:
        st.warning("No hay operaciones disponibles para generar el informe.")
        return
    
    st.info(f"Total de operaciones a incluir: {len(df_operaciones):,}")
    
    st.subheader("Seleccionar Reportes a Incluir")
    
    reportes = {
        "Top 10 por Columnas": st.checkbox("Top 10 por Columnas", value=True),
        "Post Transferencia Internacional": st.checkbox("Post Transferencia Internacional"),
        "Ejecutantes Comunes": st.checkbox("Ejecutantes Comunes"),
        "Ordenantes Comunes": st.checkbox("Ordenantes Comunes"),
        "Beneficiarios Comunes": st.checkbox("Beneficiarios Comunes"),
        "Ranking Ejecutantes": st.checkbox("Ranking Ejecutantes"),
        "Ranking Ordenantes": st.checkbox("Ranking Ordenantes"),
        "Ranking Beneficiarios": st.checkbox("Ranking Beneficiarios"),
        "Porcentaje Efectivo": st.checkbox("Porcentaje Efectivo"),
        "Cuentas Ordenantes Comunes": st.checkbox("Cuentas Ordenantes Comunes"),
        "Cuentas Beneficiarias Comunes": st.checkbox("Cuentas Beneficiarias Comunes"),
        "Operaciones Simultáneas": st.checkbox("Operaciones Simultáneas"),
        "Ranking Operaciones": st.checkbox("Ranking Operaciones"),
        "Actividad Ejecutantes": st.checkbox("Actividad Ejecutantes"),
        "Actividad Ordenantes": st.checkbox("Actividad Ordenantes"),
        "Actividad Beneficiarios": st.checkbox("Actividad Beneficiarios"),
        "Actividades Riesgo": st.checkbox("Actividades Riesgo"),
        "Ranking Agencias": st.checkbox("Ranking Agencias")
    }
    
    if st.button("🚀 Generar Informe PDF", type="primary"):
        with st.spinner("Generando informe..."):
            try:
                analizador = AnalizadorUIF(df_operaciones)
                # Nombre genérico ya que no hay caso seleccionado
                informe = GeneradorInforme("Reporte General", "Análisis de toda la base de datos")
                
                informe.agregar_portada()
                
                informe.agregar_seccion(
                    "Resumen Ejecutivo",
                    f"Este informe contiene el análisis completo de la base de datos disponible. "
                    f"Se analizaron un total de {len(df_operaciones):,} operaciones."
                )
                
                stats_generales = {
                    "Total Operaciones": len(df_operaciones),
                    "Monto Total": df_operaciones['mtotrx'].sum(),
                    "Clientes Únicos": df_operaciones['CODUNICOCLI_13_enc'].nunique(),
                    "Período": f"{df_operaciones['fec_operacion'].min()} a {df_operaciones['fec_operacion'].max()}"
                }
                informe.agregar_estadisticas(stats_generales, "Estadísticas Generales")
                
                if reportes["Top 10 por Columnas"]:
                    resultados = analizador.reporte_top10_columnas()
                    for nombre, df in resultados.items():
                        informe.agregar_tabla(df, f"Top 10 - {nombre.replace('_', ' ').title()}")
                
                if reportes["Post Transferencia Internacional"]:
                    ranking, stats = analizador.reporte_2_ranking_post_transferencia_internacional()
                    if not ranking.empty:
                        informe.agregar_seccion("Post Transferencia Internacional", 
                            f"Se encontraron {stats['total_recepciones']} transferencias internacionales, "
                            f"de las cuales {stats['total_con_operacion_posterior']} tuvieron operaciones posteriores "
                            f"({stats['porcentaje']:.2f}%).")
                        informe.agregar_tabla(ranking, "Ranking de Operaciones Posteriores")
                
                if reportes["Ejecutantes Comunes"]:
                    resultado = analizador.reporte_3_ejecutantes_comunes()
                    if not resultado.empty:
                        informe.agregar_tabla(resultado, "Ejecutantes Comunes entre Clientes")
                
                if reportes["Ordenantes Comunes"]:
                    resultado = analizador.reporte_4_ordenantes_comunes()
                    if not resultado.empty:
                        informe.agregar_tabla(resultado, "Ordenantes Comunes entre Clientes")
                
                if reportes["Beneficiarios Comunes"]:
                    resultado = analizador.reporte_5_beneficiarios_comunes()
                    if not resultado.empty:
                        informe.agregar_tabla(resultado, "Beneficiarios Comunes entre Clientes")
                
                if reportes["Ranking Ejecutantes"]:
                    ranking = analizador.reporte_6_ranking_ejecutantes()
                    if not ranking.empty:
                        informe.agregar_tabla(ranking, "Ranking de Ejecutantes")
                
                if reportes["Ranking Ordenantes"]:
                    ranking = analizador.reporte_7_ranking_ordenantes()
                    if not ranking.empty:
                        informe.agregar_tabla(ranking, "Ranking de Ordenantes")
                
                if reportes["Ranking Beneficiarios"]:
                    ranking = analizador.reporte_8_ranking_beneficiarios()
                    if not ranking.empty:
                        informe.agregar_tabla(ranking, "Ranking de Beneficiarios")
                
                if reportes["Porcentaje Efectivo"]:
                    resultado = analizador.reporte_9_porcentaje_efectivo()
                    if not resultado.empty:
                        informe.agregar_tabla(resultado, "Porcentaje de Efectivo por Cliente")
                
                if reportes["Cuentas Ordenantes Comunes"]:
                    resultado = analizador.reporte_10_cuentas_ordenantes_comunes()
                    if not resultado.empty:
                        informe.agregar_tabla(resultado, "Cuentas Ordenantes Comunes")
                
                if reportes["Cuentas Beneficiarias Comunes"]:
                    resultado = analizador.reporte_11_cuentas_beneficiarias_comunes()
                    if not resultado.empty:
                        informe.agregar_tabla(resultado, "Cuentas Beneficiarias Comunes")
                
                if reportes["Operaciones Simultáneas"]:
                    resultado, stats = analizador.reporte_12_operaciones_simultaneas()
                    if not resultado.empty:
                        informe.agregar_estadisticas(stats, "Estadísticas Operaciones Simultáneas")
                        informe.agregar_tabla(resultado, "Operaciones Simultáneas")
                
                if reportes["Ranking Operaciones"]:
                    ranking_cant, ranking_monto = analizador.reporte_13_ranking_operaciones()
                    if not ranking_cant.empty:
                        informe.agregar_tabla(ranking_cant, "Ranking de Operaciones por Cantidad")
                        informe.agregar_tabla(ranking_monto, "Ranking de Operaciones por Monto")
                
                if reportes["Actividad Ejecutantes"]:
                    ranking_cant, ranking_monto = analizador.reporte_14_actividad_ejecutantes()
                    if not ranking_cant.empty:
                        informe.agregar_tabla(ranking_cant, "Actividad Económica Ejecutantes - Por Cantidad")
                
                if reportes["Actividad Ordenantes"]:
                    ranking_cant, ranking_monto = analizador.reporte_15_actividad_ordenantes()
                    if not ranking_cant.empty:
                        informe.agregar_tabla(ranking_cant, "Actividad Económica Ordenantes - Por Cantidad")
                
                if reportes["Actividad Beneficiarios"]:
                    ranking_cant, ranking_monto = analizador.reporte_16_actividad_beneficiarios()
                    if not ranking_cant.empty:
                        informe.agregar_tabla(ranking_cant, "Actividad Económica Beneficiarios - Por Cantidad")
                
                if reportes["Actividades Riesgo"]:
                    resultados = analizador.reporte_17_actividades_riesgo()
                    if not resultados['bombas_compresores'].empty:
                        informe.agregar_hallazgo(
                            "Actividad de Riesgo: Bombas/Compresores",
                            f"Se detectaron {len(resultados['bombas_compresores'])} clientes relacionados con actividades de bombas/compresores.",
                            "ALTO"
                        )
                        informe.agregar_tabla(resultados['bombas_compresores'], "Clientes - Bombas/Compresores")
                    
                    if not resultados['seguridad_privada'].empty:
                        informe.agregar_hallazgo(
                            "Actividad de Riesgo: Seguridad Privada",
                            f"Se detectaron {len(resultados['seguridad_privada'])} clientes relacionados con seguridad privada.",
                            "MEDIO"
                        )
                        informe.agregar_tabla(resultados['seguridad_privada'], "Clientes - Seguridad Privada")
                    
                    if not resultados['transporte'].empty:
                        informe.agregar_hallazgo(
                            "Actividad de Riesgo: Transporte",
                            f"Se detectaron {len(resultados['transporte'])} clientes con transacciones de transporte >10k PEN o >3k USD.",
                            "MEDIO"
                        )
                        informe.agregar_tabla(resultados['transporte'], "Clientes - Transporte")
                
                if reportes["Ranking Agencias"]:
                    ranking = analizador.reporte_18_ranking_agencias()
                    if not ranking.empty:
                        informe.agregar_tabla(ranking, "Ranking de Agencias")
                
                pdf_buffer = informe.generar_pdf_bytes()
                
                st.success("✅ Informe generado exitosamente")
                
                st.download_button(
                    label="📥 Descargar Informe PDF",
                    data=pdf_buffer,
                    file_name=f"informe_general_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
            
            except Exception as e:
                st.error(f"Error al generar informe: {str(e)}")

def main():
    st.sidebar.title("🔍 Sistema Análisis")
    
    menu = st.sidebar.radio(
        "Menú Principal",
        ["Carga de Datos", "Gestión de Casos", "Análisis", "Generar Informe PDF"]
    )
    
    if menu == "Carga de Datos":
        pagina_carga_datos()
    elif menu == "Gestión de Casos":
        pagina_gestion_casos()
    elif menu == "Análisis":
        pagina_analisis()
    elif menu == "Generar Informe PDF":
        pagina_informe()

if __name__ == "__main__":
    main()