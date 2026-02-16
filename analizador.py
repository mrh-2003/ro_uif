import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class AnalizadorUIF:
    def __init__(self, df_operaciones):
        self.df = df_operaciones.copy()
        if 'mtotrx' in self.df.columns:
            self.df['mtotrx'] = pd.to_numeric(self.df['mtotrx'], errors='coerce')
        if 'fec_operacion' in self.df.columns:
            self.df['fec_operacion'] = pd.to_datetime(self.df['fec_operacion'], errors='coerce')
        if 'hora_operacion' in self.df.columns:
            self.df['hora_operacion'] = pd.to_datetime(self.df['hora_operacion'], format='%H:%M:%S', errors='coerce').dt.time
    
    def reporte_2_ranking_post_transferencia_internacional(self):
        df_recepcion = self.df[self.df['destipopereportesbs'] == 'TRANSFERENCIAS INTERNACIONALES (RECEPCION DE FONDOS)'].copy()
        
        if df_recepcion.empty:
            return pd.DataFrame(), {}
        
        df_recepcion = df_recepcion.sort_values(['CODUNICOCLI_13_enc', 'fec_operacion', 'hora_operacion'])
        
        resultados = []
        
        for cliente in df_recepcion['CODUNICOCLI_13_enc'].unique():
            df_cliente = self.df[self.df['CODUNICOCLI_13_enc'] == cliente].sort_values(['fec_operacion', 'hora_operacion'])
            recepciones = df_recepcion[df_recepcion['CODUNICOCLI_13_enc'] == cliente]
            
            for idx, recepcion in recepciones.iterrows():
                fecha_recepcion = recepcion['fec_operacion']
                hora_recepcion = recepcion['hora_operacion']
                
                ops_posteriores = df_cliente[
                    (df_cliente['fec_operacion'] > fecha_recepcion) |
                    ((df_cliente['fec_operacion'] == fecha_recepcion) & 
                     (df_cliente['hora_operacion'] > hora_recepcion))
                ]
                
                if not ops_posteriores.empty:
                    siguiente_op = ops_posteriores.iloc[0]
                    resultados.append({
                        'cliente': cliente,
                        'monto_recepcion': recepcion['mtotrx'],
                        'fecha_recepcion': fecha_recepcion,
                        'operacion_siguiente': siguiente_op['destipopereportesbs'],
                        'monto_siguiente': siguiente_op['mtotrx'],
                        'fecha_siguiente': siguiente_op['fec_operacion']
                    })
        
        df_resultado = pd.DataFrame(resultados)
        
        if df_resultado.empty:
            return pd.DataFrame(), {}
        
        ranking = df_resultado.groupby('operacion_siguiente').agg({
            'cliente': 'count',
            'monto_siguiente': 'sum'
        }).rename(columns={
            'cliente': 'cantidad_operaciones',
            'monto_siguiente': 'monto_total'
        }).sort_values('cantidad_operaciones', ascending=False)
        
        stats = {
            'total_recepciones': len(df_recepcion),
            'total_con_operacion_posterior': len(df_resultado),
            'porcentaje': len(df_resultado) / len(df_recepcion) * 100 if len(df_recepcion) > 0 else 0
        }
        
        return ranking, stats
    
    def reporte_3_ejecutantes_comunes(self):
        df_ejecutantes = self.df[self.df['doc_ejecutante_encriptado'].notna()].copy()
        
        agrupado = df_ejecutantes.groupby('doc_ejecutante_encriptado').agg({
            'CODUNICOCLI_13_enc': lambda x: list(x.unique()),
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupSOL': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'CODUNICOCLI_13_enc': 'clientes_diferentes',
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupSOL': 'actividad'
        })
        
        agrupado['cantidad_clientes'] = agrupado['clientes_diferentes'].apply(len)
        resultado = agrupado[agrupado['cantidad_clientes'] > 1].sort_values('cantidad_clientes', ascending=False)
        
        return resultado
    
    def reporte_4_ordenantes_comunes(self):
        df_ordenantes = self.df[self.df['doc_ordenante_encriptado'].notna()].copy()
        
        agrupado = df_ordenantes.groupby('doc_ordenante_encriptado').agg({
            'CODUNICOCLI_13_enc': lambda x: list(x.unique()),
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupOrd': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'CODUNICOCLI_13_enc': 'clientes_diferentes',
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupOrd': 'actividad'
        })
        
        agrupado['cantidad_clientes'] = agrupado['clientes_diferentes'].apply(len)
        resultado = agrupado[agrupado['cantidad_clientes'] > 1].sort_values('cantidad_clientes', ascending=False)
        
        return resultado
    
    def reporte_5_beneficiarios_comunes(self):
        df_beneficiarios = self.df[self.df['doc_beneficiario_encriptado'].notna()].copy()
        
        agrupado = df_beneficiarios.groupby('doc_beneficiario_encriptado').agg({
            'CODUNICOCLI_13_enc': lambda x: list(x.unique()),
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupBen': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'CODUNICOCLI_13_enc': 'clientes_diferentes',
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupBen': 'actividad'
        })
        
        agrupado['cantidad_clientes'] = agrupado['clientes_diferentes'].apply(len)
        resultado = agrupado[agrupado['cantidad_clientes'] > 1].sort_values('cantidad_clientes', ascending=False)
        
        return resultado
    
    def reporte_6_ranking_ejecutantes(self):
        df_ejecutantes = self.df[self.df['doc_ejecutante_encriptado'].notna()].copy()
        
        ranking = df_ejecutantes.groupby(['doc_ejecutante_encriptado', 'DesOcupSOL']).agg({
            'mtotrx': 'sum',
            'id_operacion': 'count'
        }).rename(columns={
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones'
        }).sort_values('num_operaciones', ascending=False)
        
        return ranking
    
    def reporte_7_ranking_ordenantes(self):
        df_ordenantes = self.df[self.df['doc_ordenante_encriptado'].notna()].copy()
        
        ranking = df_ordenantes.groupby([
            'doc_ordenante_encriptado', 
            'DesOcupOrd',
            'DepOrd',
            'ProvOrd',
            'DisOrd'
        ]).agg({
            'mtotrx': 'sum',
            'id_operacion': 'count'
        }).rename(columns={
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones'
        }).sort_values('num_operaciones', ascending=False)
        
        return ranking
    
    def reporte_8_ranking_beneficiarios(self):
        df_beneficiarios = self.df[self.df['doc_beneficiario_encriptado'].notna()].copy()
        
        ranking = df_beneficiarios.groupby([
            'doc_beneficiario_encriptado',
            'DesOcupBen',
            'DepBen',
            'ProvBen',
            'DisBen'
        ]).agg({
            'mtotrx': 'sum',
            'id_operacion': 'count'
        }).rename(columns={
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones'
        }).sort_values('num_operaciones', ascending=False)
        
        return ranking
    
    def reporte_9_porcentaje_efectivo(self):
        resultado = self.df.groupby('CODUNICOCLI_13_enc').agg({
            'id_operacion': 'count',
            'desorigendinero': lambda x: x.notna().sum(),
            'mtotrx': 'sum'
        }).rename(columns={
            'id_operacion': 'total_operaciones',
            'desorigendinero': 'operaciones_efectivo',
            'mtotrx': 'monto_total'
        })
        
        resultado['porcentaje_efectivo'] = (resultado['operaciones_efectivo'] / resultado['total_operaciones'] * 100).round(2)
        
        df_efectivo = self.df[self.df['desorigendinero'].notna()].groupby('CODUNICOCLI_13_enc')['mtotrx'].sum()
        resultado['monto_efectivo'] = df_efectivo
        resultado['monto_efectivo'] = resultado['monto_efectivo'].fillna(0)
        resultado['porcentaje_monto_efectivo'] = (resultado['monto_efectivo'] / resultado['monto_total'] * 100).round(2)
        
        return resultado.sort_values('porcentaje_efectivo', ascending=False)
    
    def reporte_10_cuentas_ordenantes_comunes(self):
        df_cuentas = self.df[self.df['codcta20ordenante'].notna()].copy()
        
        agrupado = df_cuentas.groupby('codcta20ordenante').agg({
            'CODUNICOCLI_13_enc': lambda x: list(x.unique()),
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupOrd': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'CODUNICOCLI_13_enc': 'clientes_diferentes',
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupOrd': 'actividad'
        })
        
        agrupado['cantidad_clientes'] = agrupado['clientes_diferentes'].apply(len)
        resultado = agrupado[agrupado['cantidad_clientes'] > 1].sort_values('cantidad_clientes', ascending=False)
        
        return resultado
    
    def reporte_11_cuentas_beneficiarias_comunes(self):
        df_cuentas = self.df[self.df['codcta20beneficiario'].notna()].copy()
        
        agrupado = df_cuentas.groupby('codcta20beneficiario').agg({
            'CODUNICOCLI_13_enc': lambda x: list(x.unique()),
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupBen': lambda x: x.mode()[0] if not x.mode().empty else ''
        }).rename(columns={
            'CODUNICOCLI_13_enc': 'clientes_diferentes',
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupBen': 'actividad'
        })
        
        agrupado['cantidad_clientes'] = agrupado['clientes_diferentes'].apply(len)
        resultado = agrupado[agrupado['cantidad_clientes'] > 1].sort_values('cantidad_clientes', ascending=False)
        
        return resultado
    
    def reporte_12_operaciones_simultaneas(self, minutos=30):
        # Asegurar ordenamiento
        df_sorted = self.df.sort_values(['CODUNICOCLI_13_enc', 'fec_operacion', 'hora_operacion'])
        
        resultados = []
        
        # Palabras clave para identificar tipos de operación
        # Se asume que todo lo que no es ingreso explícito podría ser una salida si mueve fondos
        # Pero para ser precisos, buscaremos salidas explícitas para confirmar "disposición"
        
        def es_ingreso(descripcion):
            d = str(descripcion).upper()
            return any(x in d for x in ['RECEPCION', 'DEPOSITO', 'ABONO', 'CREDITO', 'ENTRADA'])

        def es_egreso(descripcion):
            d = str(descripcion).upper()
            # Si es transferencia y no dice recepción/entrada, asumimos salida
            if 'TRANSFERENCIA' in d and not any(x in d for x in ['RECEPCION', 'ENTRADA', 'RECIBID']):
                return True
            return any(x in d for x in ['RETIRO', 'ENVIO', 'PAGO', 'DEBITO', 'SALIDA', 'CHEQUE'])
        
        for cliente in df_sorted['CODUNICOCLI_13_enc'].unique():
            df_cliente = df_sorted[df_sorted['CODUNICOCLI_13_enc'] == cliente].copy()
            
            # Crear columna datetime robusta
            try:
                # Convertir a string y combinar, manejando NaNs
                fec = df_cliente['fec_operacion'].astype(str)
                hora = df_cliente['hora_operacion'].astype(str)
                df_cliente['datetime'] = pd.to_datetime(fec + ' ' + hora, errors='coerce')
            except Exception:
                continue
                
            # Filtrar filas donde datetime falló
            df_cliente = df_cliente.dropna(subset=['datetime'])
            
            if df_cliente.empty:
                continue

            for i in range(len(df_cliente) - 1):
                op1 = df_cliente.iloc[i]
                desc1 = op1['destipopereportesbs']
                
                # Solo analizamos si la operación inicial es un INGRESO
                if not es_ingreso(desc1):
                    continue
                
                tiempo_limite = op1['datetime'] + timedelta(minutes=minutos)
                
                # Buscar operaciones posteriores dentro de la ventana de tiempo
                # que sean EGRESOS (disposición de fondos)
                ops_candidatas = df_cliente[
                    (df_cliente['datetime'] > op1['datetime']) & 
                    (df_cliente['datetime'] <= tiempo_limite)
                ]
                
                if ops_candidatas.empty:
                    continue
                    
                # Filtramos solo las que son egresos
                ops_egresos = ops_candidatas[ops_candidatas['destipopereportesbs'].apply(es_egreso)]
                
                if ops_egresos.empty:
                    continue
                
                monto_dispuesto = ops_egresos['mtotrx'].sum()
                
                # Evitar división por cero
                if op1['mtotrx'] <= 0:
                    continue
                    
                porcentaje = (monto_dispuesto / op1['mtotrx'] * 100)
                
                # Umbral reducido al 50% ("mayor parte")
                if porcentaje >= 50:
                    # Resumen de operaciones de salida
                    ops_detalle = ops_egresos['destipopereportesbs'].value_counts().to_dict()
                    str_ops = ", ".join([f"{k} (x{v})" for k, v in ops_detalle.items()])
                    
                    resultados.append({
                        'cliente': cliente,
                        'fecha_recepcion': op1['fec_operacion'],
                        'hora_recepcion': op1['hora_operacion'],
                        'tipo_recepcion': desc1,
                        'monto_recibido': op1['mtotrx'],
                        'monto_dispuesto': monto_dispuesto,
                        'porcentaje_dispuesto': round(porcentaje, 2),
                        'tiempo_transcurrido_min': round((ops_egresos['datetime'].max() - op1['datetime']).total_seconds() / 60, 1),
                        'cantidad_operaciones_salida': len(ops_egresos),
                        'detalle_salidas': str_ops,
                        'alerta': 'Posible Testaferro/Intermediario'
                    })
        
        df_resultado = pd.DataFrame(resultados)
        
        if df_resultado.empty:
            return pd.DataFrame(), {}
        
        stats = {
            'total_casos': len(df_resultado),
            'promedio_porcentaje': df_resultado['porcentaje_dispuesto'].mean(),
            'monto_total_recibido': df_resultado['monto_recibido'].sum(),
            'monto_total_dispuesto': df_resultado['monto_dispuesto'].sum()
        }
        
        return df_resultado, stats
    
    def reporte_13_ranking_operaciones(self):
        ranking_cantidad = self.df.groupby('destipopereportesbs').agg({
            'id_operacion': 'count',
            'mtotrx': 'sum'
        }).rename(columns={
            'id_operacion': 'cantidad_operaciones',
            'mtotrx': 'monto_total'
        }).sort_values('cantidad_operaciones', ascending=False)
        
        ranking_monto = ranking_cantidad.sort_values('monto_total', ascending=False)
        
        return ranking_cantidad, ranking_monto
    
    def reporte_14_actividad_ejecutantes(self):
        df_ejecutantes = self.df[self.df['DesOcupSOL'].notna()].copy()
        
        ranking_cantidad = df_ejecutantes.groupby('DesOcupSOL').agg({
            'id_operacion': 'count',
            'mtotrx': 'sum'
        }).rename(columns={
            'id_operacion': 'cantidad_operaciones',
            'mtotrx': 'monto_total'
        }).sort_values('cantidad_operaciones', ascending=False)
        
        ranking_monto = ranking_cantidad.sort_values('monto_total', ascending=False)
        
        return ranking_cantidad, ranking_monto
    
    def reporte_15_actividad_ordenantes(self):
        df_ordenantes = self.df[self.df['DesOcupOrd'].notna()].copy()
        
        ranking_cantidad = df_ordenantes.groupby('DesOcupOrd').agg({
            'id_operacion': 'count',
            'mtotrx': 'sum'
        }).rename(columns={
            'id_operacion': 'cantidad_operaciones',
            'mtotrx': 'monto_total'
        }).sort_values('cantidad_operaciones', ascending=False)
        
        ranking_monto = ranking_cantidad.sort_values('monto_total', ascending=False)
        
        return ranking_cantidad, ranking_monto
    
    def reporte_16_actividad_beneficiarios(self):
        df_beneficiarios = self.df[self.df['DesOcupBen'].notna()].copy()
        
        ranking_cantidad = df_beneficiarios.groupby('DesOcupBen').agg({
            'id_operacion': 'count',
            'mtotrx': 'sum'
        }).rename(columns={
            'id_operacion': 'cantidad_operaciones',
            'mtotrx': 'monto_total'
        }).sort_values('cantidad_operaciones', ascending=False)
        
        ranking_monto = ranking_cantidad.sort_values('monto_total', ascending=False)
        
        return ranking_cantidad, ranking_monto
    
    def reporte_17_actividades_riesgo(self):
        resultados = {}
        
        df_ben = self.df[self.df['DesOcupBen'].notna()].copy()
        
        bombas = df_ben[df_ben['DesOcupBen'].str.contains('BOMBAS|COMPRESORES|GRIFOS|VALVULAS', case=False, na=False)]
        resultados['bombas_compresores'] = bombas.groupby('CODUNICOCLI_13_enc').agg({
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupBen': lambda x: list(x.unique())
        }).rename(columns={
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupBen': 'actividades'
        })
        
        seguridad = df_ben[df_ben['DesOcupBen'].str.contains('SEGURIDAD PRIVADA', case=False, na=False)]
        resultados['seguridad_privada'] = seguridad.groupby('CODUNICOCLI_13_enc').agg({
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupBen': lambda x: list(x.unique())
        }).rename(columns={
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupBen': 'actividades'
        })
        
        transporte = df_ben[
            (df_ben['DesOcupBen'].str.contains('TRANSP', case=False, na=False)) &
            (df_ben['mtotrx'] >= 10000)
        ]
        
        transporte_usd = df_ben[
            (df_ben['DesOcupBen'].str.contains('TRANSP', case=False, na=False)) &
            (df_ben['nbrmonedadestino'].str.contains('DOLAR', case=False, na=False)) &
            (df_ben['mtotrx'] >= 3000)
        ]
        
        resultados['transporte'] = pd.concat([transporte, transporte_usd]).drop_duplicates().groupby('CODUNICOCLI_13_enc').agg({
            'mtotrx': 'sum',
            'id_operacion': 'count',
            'DesOcupBen': lambda x: list(x.unique())
        }).rename(columns={
            'mtotrx': 'monto_total',
            'id_operacion': 'num_operaciones',
            'DesOcupBen': 'actividades'
        })
        
        return resultados
    
    def reporte_18_ranking_agencias(self):
        df_agencias = self.df[self.df['codigo_ubigeo'].notna()].copy()
        
        ranking = df_agencias.groupby('codigo_ubigeo').agg({
            'id_operacion': 'count',
            'mtotrx': 'sum',
            'CODUNICOCLI_13_enc': 'nunique'
        }).rename(columns={
            'id_operacion': 'cantidad_operaciones',
            'mtotrx': 'monto_total',
            'CODUNICOCLI_13_enc': 'clientes_unicos'
        }).sort_values('cantidad_operaciones', ascending=False)
        
        return ranking
    
    def reporte_19_actividad_mineria(self):
        # Filtrar operacions donde el origen del dinero tiene "minera" o "mineria" (case insensitive)
        mask = self.df['desorigendinero'].fillna('').str.contains('minera|mineria', case=False, regex=True)
        df_mineria = self.df[mask].copy()
        
        resultados = {}
        
        # Helper para agrupar
        def agrupar_por_actividad(df, col_actividad):
            if df.empty or col_actividad not in df.columns:
                return pd.DataFrame()
            
            return df.groupby(col_actividad).agg({
                'id_operacion': 'count',
                'mtotrx': 'sum',
                'CODUNICOCLI_13_enc': 'nunique'
            }).rename(columns={
                'id_operacion': 'cantidad_operaciones',
                'mtotrx': 'monto_total',
                'CODUNICOCLI_13_enc': 'clientes_unicos'
            }).sort_values('cantidad_operaciones', ascending=False)
            
        resultados['ejecutantes'] = agrupar_por_actividad(df_mineria, 'DesOcupSOL')
        resultados['ordenantes'] = agrupar_por_actividad(df_mineria, 'DesOcupOrd')
        resultados['beneficiarios'] = agrupar_por_actividad(df_mineria, 'DesOcupBen')
        
        return resultados, len(df_mineria)
    
    def reporte_top10_columnas(self):
        resultados = {}
        
        if 'SEGMENTO' in self.df.columns:
            seg = self.df.groupby('SEGMENTO').agg({
                'id_operacion': 'count',
                'mtotrx': 'sum'
            }).rename(columns={'id_operacion': 'cantidad', 'mtotrx': 'monto_total'})
            
            df_sol = self.df[self.df['nbrmonedadestino'].str.contains('SOL', case=False, na=False)]
            df_usd = self.df[self.df['nbrmonedadestino'].str.contains('DOLAR', case=False, na=False)]
            
            seg['monto_soles'] = df_sol.groupby('SEGMENTO')['mtotrx'].sum()
            seg['monto_dolares'] = df_usd.groupby('SEGMENTO')['mtotrx'].sum()
            seg = seg.fillna(0)
            
            resultados['segmento'] = seg.sort_values('cantidad', ascending=False).head(10)
        
        if 'ACT_ECONOMICA' in self.df.columns:
            act = self.df[self.df['ACT_ECONOMICA'].notna()].groupby('ACT_ECONOMICA').agg({
                'id_operacion': 'count',
                'mtotrx': 'sum'
            }).rename(columns={'id_operacion': 'cantidad', 'mtotrx': 'monto_total'})
            resultados['actividad_economica'] = act.sort_values('cantidad', ascending=False).head(10)
        
        if 'destipopereportesbs' in self.df.columns:
            ops = self.df.groupby('destipopereportesbs').agg({
                'id_operacion': 'count',
                'mtotrx': 'sum'
            }).rename(columns={'id_operacion': 'cantidad', 'mtotrx': 'monto_total'})
            resultados['tipo_operacion'] = ops.sort_values('cantidad', ascending=False).head(10)
        
        if 'descanal' in self.df.columns:
            canales = self.df.groupby('descanal').agg({
                'id_operacion': 'count',
                'mtotrx': 'sum'
            }).rename(columns={'id_operacion': 'cantidad', 'mtotrx': 'monto_total'})
            resultados['canal'] = canales.sort_values('cantidad', ascending=False).head(10)
        
        if 'DesOcupOrd' in self.df.columns:
            ord_act = self.df[self.df['DesOcupOrd'].notna()].groupby('DesOcupOrd').agg({
                'id_operacion': 'count',
                'mtotrx': 'sum'
            }).rename(columns={'id_operacion': 'cantidad', 'mtotrx': 'monto_total'})
            resultados['actividad_ordenante'] = ord_act.sort_values('cantidad', ascending=False).head(10)
        
        if 'DesOcupBen' in self.df.columns:
            ben_act = self.df[self.df['DesOcupBen'].notna()].groupby('DesOcupBen').agg({
                'id_operacion': 'count',
                'mtotrx': 'sum'
            }).rename(columns={'id_operacion': 'cantidad', 'mtotrx': 'monto_total'})
            resultados['actividad_beneficiario'] = ben_act.sort_values('cantidad', ascending=False).head(10)
        
        return resultados
