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
    
    def reporte_2_ranking_post_transferencia_internacional(self, dias_seguimiento=7):
        df_recepcion = self.df[self.df['destipopereportesbs'] == 'TRANSFERENCIAS INTERNACIONALES (RECEPCION DE FONDOS)'].copy()
        
        if df_recepcion.empty:
            return pd.DataFrame(), {}, []
        
        # Asegurar orden
        df_recepcion = df_recepcion.sort_values(['CODUNICOCLI_13_enc', 'fec_operacion', 'hora_operacion'])
        
        # Helper para identificar salidas (reutilizando lógica similar a operaciones simultáneas)
        def es_salida(desc):
            d = str(desc).upper()
            if 'TRANSFERENCIA' in d and not any(x in d for x in ['RECEPCION', 'ENTRADA', 'RECIBID', 'ABONO']):
                return True
            return any(x in d for x in ['RETIRO', 'ENVIO', 'PAGO', 'DEBITO', 'SALIDA', 'CHEQUE', 'EFECTIVO'])

        resultados_agrupados = []
        first_ops = [] # Para el ranking global

        for cliente in df_recepcion['CODUNICOCLI_13_enc'].unique():
            # Filtrar y ordenar operaciones del cliente
            df_cliente = self.df[self.df['CODUNICOCLI_13_enc'] == cliente].sort_values(['fec_operacion', 'hora_operacion']).reset_index(drop=True)
            
            # Obtener índices de las recepciones internacionales
            indices_recepciones = df_cliente.index[
                df_cliente['destipopereportesbs'] == 'TRANSFERENCIAS INTERNACIONALES (RECEPCION DE FONDOS)'
            ].tolist()
            
            if not indices_recepciones:
                continue
                
            for i, idx_recepcion in enumerate(indices_recepciones):
                recepcion = df_cliente.iloc[idx_recepcion]
                
                fecha_recepcion = recepcion['fec_operacion']
                # Si hora es NaT o similar, asumir inicio del día para la ventana
                hora_recepcion = recepcion['hora_operacion']
                
                # Definir límite por tiempo (días de seguimiento)
                fecha_limite_dias = fecha_recepcion + timedelta(days=dias_seguimiento)
                
                # Definir límite por siguiente recepción (si existe)
                idx_siguiente_recepcion = indices_recepciones[i+1] if i + 1 < len(indices_recepciones) else len(df_cliente)
                
                # Segmento de operaciones potenciales: desde la siguiente fila hasta antes de la próxima recepción
                # IMPORTANTE: El segmento termina en idx_siguiente_recepcion (no inclusivo)
                segmento = df_cliente.iloc[idx_recepcion + 1 : idx_siguiente_recepcion].copy()
                
                if segmento.empty:
                    continue
                    
                # Aplicar filtro de fecha (hasta N días)
                # Nota: Asumimos que están ordenados, pero filtramos explícitamente por seguridad
                segmento = segmento[segmento['fec_operacion'] <= fecha_limite_dias]
                
                if segmento.empty:
                    continue
                
                # 1. Para estadísticas globales (primera op inmediatamente siguiente)
                first_op = segmento.iloc[0]
                first_ops.append({
                    'operacion_siguiente': first_op['destipopereportesbs'],
                    'monto_siguiente': first_op['mtotrx'],
                    'cliente': cliente
                })
                
                # 2. Filtrar SALIDAS
                ops_salidas = segmento[segmento['destipopereportesbs'].apply(es_salida)].copy()
                
                if not ops_salidas.empty:
                    # Seleccionar y renombrar columnas solicitadas
                    columnas_deseadas = {
                        'destipopereportesbs': 'Tipo Transacción',
                        'doc_beneficiario_encriptado': 'Beneficiario',
                        'doc_ordenante_encriptado': 'Ordenante',
                        'doc_ejecutante_encriptado': 'Ejecutante',
                        'fec_operacion': 'Fecha',
                        'hora_operacion': 'Hora',
                        'mtotrx': 'Monto',
                        'nbrmonedadestino': 'Moneda',
                        'DesOcupBen': 'Ocupación Ben.',
                        'DesOcupSOL': 'Ocupación Sol.',
                        'DesOcupOrd': 'Ocupación Ord.',
                        'descanal': 'Canal',
                        'ACT_ECONOMICA': 'Actividad Económica'
                    }
                    
                    # Filtrar columnas que realmente existen en el DF
                    cols_to_keep = [c for c in columnas_deseadas.keys() if c in ops_salidas.columns]
                    ops_display = ops_salidas[cols_to_keep].rename(columns=columnas_deseadas)
                    
                    # Formatear Fechas para que se vean bien
                    if 'Fecha' in ops_display.columns:
                        ops_display['Fecha'] = ops_display['Fecha'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
                    
                    # Guardamos el caso completo
                    resultados_agrupados.append({
                        'cliente': cliente,
                        'entrada': recepcion,
                        'salidas': ops_display
                    })
        
        # Generar Ranking (Compatibilidad)
        df_first_ops = pd.DataFrame(first_ops)
        if not df_first_ops.empty:
            ranking = df_first_ops.groupby('operacion_siguiente').agg({
                'cliente': 'count',
                'monto_siguiente': 'sum'
            }).rename(columns={
                'cliente': 'cantidad_operaciones',
                'monto_siguiente': 'monto_total'
            }).sort_values('cantidad_operaciones', ascending=False)
        else:
            ranking = pd.DataFrame()
        
        stats = {
            'total_recepciones': len(df_recepcion),
            'total_con_salidas': len(resultados_agrupados),
            'porcentaje': (len(resultados_agrupados) / len(df_recepcion) * 100) if len(df_recepcion) > 0 else 0
        }
        
        return ranking, stats, resultados_agrupados
    
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
    
    def reporte_12_operaciones_simultaneas(self, minutos=30, tolerancia_porcentaje=10, min_ops=1):
        # Clasificación estricta de operaciones
        INFLOWS = [
            'TRANSFERENCIAS ENTRE CUENTAS DE DIFERENTES ENTIDADES (RECEPCION DE FONDOS)',
            'COBRO DE CHEQUES DE OTRO BANCO (ABONO O PAGO)',
            'GIROS NACIONALES (RECEPCION DE FONDOS)',
            'COBRO DE CHEQUES DEL MISMO BANCO',
            'TRANSFERENCIAS INTERNACIONALES (RECEPCION DE FONDOS)',
            'DEPOSITOS EN CUENTA CORRIENTE',
            'DEPOSITOS EN CUENTA DE AHORRO',
            'DEPOSITOS CONSTITUIDOS POR TITULOS VALORES (CERTIFICADOS BANCARIOS EN MONEDA NACIONAL Y MONEDA EXTRANJERA)'
        ]
        
        OUTFLOWS = [
            'TRANSFERENCIAS ENTRE CUENTAS DE DIFERENTES ENTIDADES (ENVIO DE FONDOS)',
            'GIROS NACIONALES (ENVIO DE FONDOS)',
            'TRANSFERENCIAS INTERNACIONALES (ENVIO DE FONDOS)',
            'AMORTIZACION DE PRESTAMOS',
            'AMORTIZACION ANTICIPADA DE PRESTAMOS',
            'DEPOSITOS EN CUENTAS DE PLAZO FIJO',
            'RETIROS DE DEPOSITOS',
            'COMPRA DE CHEQUES DE GERENCIA',
            'RETIRO TOTAL DE DEPOSITOS'
        ]

        def get_tipo_flujo(desc):
            d = str(desc).strip()
            if d in INFLOWS: return 'ENTRADA'
            if d in OUTFLOWS: return 'SALIDA'
            return 'NEUTRO'

        def es_valido(nodo):
            n = str(nodo).upper()
            invalidos = ['DESCONOCIDO', 'NO REGISTRADO', 'NAN', 'NONE', '', 'NO DISPONIBLE']
            return n not in invalidos

        df_sorted = self.df.sort_values(['CODUNICOCLI_13_enc', 'fec_operacion', 'hora_operacion'])
        
        # Preparar datetime
        try:
            fec = df_sorted['fec_operacion'].astype(str)
            hora = df_sorted['hora_operacion'].astype(str)
            df_sorted['datetime'] = pd.to_datetime(fec + ' ' + hora, errors='coerce')
        except Exception:
            return pd.DataFrame(), pd.DataFrame(), {}

        df_sorted = df_sorted.dropna(subset=['datetime'])
        
        casos = []
        edges = []
        
        # Iterar por cliente
        for cliente in df_sorted['CODUNICOCLI_13_enc'].unique():
            df_cli = df_sorted[df_sorted['CODUNICOCLI_13_enc'] == cliente].copy()
            df_cli['flujo'] = df_cli['destipopereportesbs'].apply(get_tipo_flujo)
            
            # Reset index para poder usar indices numéricos para control
            df_cli = df_cli.reset_index(drop=True)
            
            used_indices = set()
            indices_list = df_cli.index.tolist()
            
            # --- PRIORIDAD 1: ENTRADA + SALIDA(S) SIMILARES ---
            for i in indices_list:
                if i in used_indices: continue
                
                row_in = df_cli.iloc[i]
                if row_in['flujo'] != 'ENTRADA': continue
                
                # Buscar salidas en ventana de tiempo
                t_start = row_in['datetime']
                t_end = t_start + timedelta(minutes=minutos)
                
                # Candidatos: Salidas, en rango de tiempo, no usadas
                mask_candidates = (
                    (df_cli['datetime'] >= t_start) & 
                    (df_cli['datetime'] <= t_end) & 
                    (df_cli['flujo'] == 'SALIDA') & 
                    (~df_cli.index.isin(used_indices))
                )
                
                candidates = df_cli[mask_candidates]
                
                if candidates.empty:
                    continue
                
                # Validar cantidad de operaciones (1 entrada + N salidas)
                total_ops_caso = 1 + len(candidates)
                # NOTA: Regla de minimo de operaciones NO APLICA para P1 (Entrada -> Salida directa)
                # if total_ops_caso < min_ops:
                #    continue

                monto_in = row_in['mtotrx']
                min_match = monto_in * (1 - tolerancia_porcentaje/100)
                max_match = monto_in * (1 + tolerancia_porcentaje/100)
                
                total_out = candidates['mtotrx'].sum()
                
                if min_match <= total_out <= max_match:
                    # Match encontrado!
                    used_indices.add(i)
                    used_indices.update(candidates.index.tolist())
                    
                    # Registrar Caso
                    caso_id = f"{cliente}-{i}-P1"
                    desc_salidas = ", ".join(candidates['destipopereportesbs'].unique())
                    casos.append({
                        'CasoID': caso_id,
                        'Prioridad': 1,
                        'Cliente': cliente,
                        'Tipo': 'Simultanea (Entrada->Salida)',
                        'Fecha': row_in['fec_operacion'],
                        'Hora': row_in['hora_operacion'],
                        'Monto Entrante': monto_in,
                        'Monto Saliente': total_out,
                        'Cantidad Operaciones': total_ops_caso,
                        'Diferencia %': round(abs(monto_in - total_out)/monto_in * 100, 2) if monto_in > 0 else 0,
                        'Detalle': f"Entrada: {row_in['destipopereportesbs']} | Salidas: {desc_salidas}"
                    })
                    
                    # Registrar Edges (Entrada -> Cliente -> Salidas)
                    origen = row_in.get('doc_ordenante_encriptado', 'Desconocido')
                    if pd.isna(origen): origen = 'Desconocido'
                    
                    if es_valido(origen) and es_valido(cliente):
                        edges.append({
                            'source': str(origen),
                            'target': str(cliente),
                            'amount': float(monto_in),
                            'label': 'Entrada (P1)',
                            'caso_id': caso_id
                        })
                    
                    for _, row_out in candidates.iterrows():
                        destino = row_out.get('doc_beneficiario_encriptado', 'Desconocido')
                        if pd.isna(destino): destino = 'Desconocido'
                        
                        if es_valido(cliente) and es_valido(destino):
                            edges.append({
                                'source': str(cliente),
                                'target': str(destino),
                                'amount': float(row_out['mtotrx']),
                                'label': 'Salida (P1)',
                                'caso_id': caso_id
                            })

            # --- PRIORIDAD 2: SOLO SALIDAS CASI INSTANTANEAS (Ráfaga) ---
            # Buscamos ráfagas de al menos 2 salidas en la ventana
            for i in indices_list:
                if i in used_indices: continue
                
                row = df_cli.iloc[i]
                if row['flujo'] != 'SALIDA': continue
                
                t_start = row['datetime']
                t_end = t_start + timedelta(minutes=minutos)
                
                mask_group = (
                    (df_cli['datetime'] >= t_start) & 
                    (df_cli['datetime'] <= t_end) & 
                    (df_cli['flujo'] == 'SALIDA') & 
                    (~df_cli.index.isin(used_indices))
                )
                
                group = df_cli[mask_group]
                
                # Deben ser al menos 2 para considerar "ráfaga"
                if len(group) >= 2:
                    
                    # Validar filtro de cantidad
                    if len(group) < min_ops:
                        continue

                    used_indices.update(group.index.tolist())
                    
                    total_amt = group['mtotrx'].sum()
                    caso_id = f"{cliente}-{i}-P2"
                    
                    casos.append({
                        'CasoID': caso_id,
                        'Prioridad': 2,
                        'Cliente': cliente,
                        'Tipo': 'Ráfaga Salidas',
                        'Fecha': row['fec_operacion'],
                        'Hora': row['hora_operacion'],
                        'Monto Entrante': 0,
                        'Monto Saliente': total_amt,
                        'Cantidad Operaciones': len(group),
                        'Diferencia %': 0,
                        'Detalle': f"{len(group)} salidas detectadas en {minutos} min"
                    })
                    
                    for _, row_out in group.iterrows():
                        destino = row_out.get('doc_beneficiario_encriptado', 'Desconocido')
                        if pd.isna(destino): destino = 'Desconocido'
                        
                        if es_valido(cliente) and es_valido(destino):
                            edges.append({
                                'source': str(cliente),
                                'target': str(destino),
                                'amount': float(row_out['mtotrx']),
                                'label': 'Salida (P2)',
                                'caso_id': caso_id
                            })

            # --- PRIORIDAD 3: SOLO ENTRADAS CASI INSTANTANEAS (Ráfaga) ---
            for i in indices_list:
                if i in used_indices: continue
                
                row = df_cli.iloc[i]
                if row['flujo'] != 'ENTRADA': continue
                
                t_start = row['datetime']
                t_end = t_start + timedelta(minutes=minutos)
                
                mask_group = (
                    (df_cli['datetime'] >= t_start) & 
                    (df_cli['datetime'] <= t_end) & 
                    (df_cli['flujo'] == 'ENTRADA') & 
                    (~df_cli.index.isin(used_indices))
                )
                
                group = df_cli[mask_group]
                
                if len(group) >= 2:
                    
                    # Validar filtro de cantidad
                    if len(group) < min_ops:
                        continue

                    used_indices.update(group.index.tolist())
                    
                    total_amt = group['mtotrx'].sum()
                    caso_id = f"{cliente}-{i}-P3"
                    
                    casos.append({
                        'CasoID': caso_id,
                        'Prioridad': 3,
                        'Cliente': cliente,
                        'Tipo': 'Ráfaga Entradas',
                        'Fecha': row['fec_operacion'],
                        'Hora': row['hora_operacion'],
                        'Monto Entrante': total_amt,
                        'Monto Saliente': 0,
                        'Cantidad Operaciones': len(group),
                        'Diferencia %': 0,
                        'Detalle': f"{len(group)} entradas detectadas en {minutos} min"
                    })
                    
                    for _, row_in_g in group.iterrows():
                        origen = row_in_g.get('doc_ordenante_encriptado', 'Desconocido')
                        if pd.isna(origen): origen = 'Desconocido'
                        
                        if es_valido(origen) and es_valido(cliente):
                            edges.append({
                                'source': str(origen),
                                'target': str(cliente),
                                'amount': float(row_in_g['mtotrx']),
                                'label': 'Entrada (P3)',
                                'caso_id': caso_id
                            })

        df_casos = pd.DataFrame(casos)
        df_edges = pd.DataFrame(edges)
        
        if df_casos.empty:
            stats = {'total_casos': 0}
        else:
            stats = {
                'total_casos': len(df_casos),
                'prioridad_1_pares': len(df_casos[df_casos['Prioridad'] == 1]),
                'prioridad_2_salidas': len(df_casos[df_casos['Prioridad'] == 2]),
                'prioridad_3_entradas': len(df_casos[df_casos['Prioridad'] == 3]),
                'monto_total_movido': df_casos['Monto Saliente'].sum() + df_casos['Monto Entrante'].sum()
            }
        
        return df_casos, df_edges, stats
    
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
