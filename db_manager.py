import sqlite3
import pandas as pd
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='uif_analysis.db'):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def cargar_datos(self, df, codigo_carga, archivo_nombre):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO cargas (codigo_carga, archivo_nombre, total_registros) VALUES (?, ?, ?)",
                (codigo_carga, archivo_nombre, len(df))
            )
            id_carga = cursor.lastrowid
            
            df['id_carga'] = id_carga
            
            columnas_db = [
                'id_carga', 'CODUNICOCLI_13_enc', 'TIPO_DE_MARCA', 'Oficio', 'Delito',
                'DESTIPDOCUMENTO', 'DESTIPBANCA', 'SEGMENTO', 'ACT_ECONOMICA',
                'CODUNICOCLI_13', 'busqueda', 'flgtipoclibusqueda',
                'destipclasifpartyrelacionado', 'descanal', 'codigo_ubigeo',
                'fec_operacion', 'hora_operacion', 'tipo_ejecutante',
                'tipo_doc_ejecutante', 'doc_ejecutante_encriptado', 'DesOcupSOL',
                'tipo_ordenante', 'tipo_doc_ordenante', 'doc_ordenante_encriptado',
                'DesOcupOrd', 'DepOrd', 'ProvOrd', 'DisOrd', 'tipo_beneficiario',
                'tipo_doc_beneficiario', 'doc_beneficiario_encriptado', 'DesOcupBen',
                'DepBen', 'ProvBen', 'DisBen', 'tipopereportesbs',
                'destipopereportesbs', 'desorigendinero', 'nbrmonedadestino',
                'mtotrx', 'codcta20ordenante', 'codcta20beneficiario'
            ]
            
            cols_existentes = [col for col in columnas_db if col in df.columns]
            df_insert = df[cols_existentes]
            
            df_insert.to_sql('operaciones', conn, if_exists='append', index=False)
            
            conn.commit()
            return True, id_carga
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def get_cargas(self):
        conn = self.get_connection()
        try:
            df = pd.read_sql("SELECT * FROM cargas ORDER BY fecha_carga DESC", conn)
        except:
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def crear_caso(self, nombre_caso, descripcion=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO casos (nombre_caso, descripcion) VALUES (?, ?)",
                (nombre_caso, descripcion)
            )
            id_caso = cursor.lastrowid
            conn.commit()
            return True, id_caso
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def agregar_clientes_a_caso(self, id_caso, clientes):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            for cliente in clientes:
                cursor.execute(
                    "INSERT INTO caso_clientes (id_caso, CODUNICOCLI_13_enc) VALUES (?, ?)",
                    (id_caso, cliente)
                )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def agregar_carga_a_caso(self, id_caso, id_carga):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO caso_cargas (id_caso, id_carga) VALUES (?, ?)",
                (id_caso, id_carga)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_casos(self):
        conn = self.get_connection()
        try:
            df = pd.read_sql("SELECT * FROM casos ORDER BY fecha_creacion DESC", conn)
        except:
            df = pd.DataFrame()
        finally:
            conn.close()
        return df
    
    def eliminar_caso(self, id_caso):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM caso_clientes WHERE id_caso = ?", (id_caso,))
            cursor.execute("DELETE FROM caso_cargas WHERE id_caso = ?", (id_caso,))
            cursor.execute("DELETE FROM casos WHERE id_caso = ?", (id_caso,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            return False
        finally:
            conn.close()

    def _aplicar_filtros_sql(self, query, params, filtros):
        if filtros:
            if filtros.get('moneda'):
                if filtros['moneda'] == 'SOL':
                    query += " AND nbrmonedadestino LIKE '%SOL%'"
                elif filtros['moneda'] == 'DOLAR':
                    query += " AND nbrmonedadestino LIKE '%DOLAR%'"
            
            if filtros.get('tipo_doc'):
                if filtros['tipo_doc'] == 'DNI':
                    query += " AND DESTIPDOCUMENTO = 'DNI'"
                elif filtros['tipo_doc'] == 'RUC':
                    query += " AND DESTIPDOCUMENTO = 'RUC'"
            
            if filtros.get('monto_min'):
                query += f" AND mtotrx >= {filtros['monto_min']}"
            
            if filtros.get('monto_max'):
                query += f" AND mtotrx <= {filtros['monto_max']}"
            
            if filtros.get('fecha_min'):
                query += f" AND fec_operacion >= '{filtros['fecha_min']}'"
            
            if filtros.get('fecha_max'):
                query += f" AND fec_operacion <= '{filtros['fecha_max']}'"
            
            if filtros.get('flgtipoclibusqueda'):
                query += f" AND flgtipoclibusqueda IN ({','.join(['?' for _ in filtros['flgtipoclibusqueda']])})"
                params.extend(filtros['flgtipoclibusqueda'])
            
            if filtros.get('destipclasifpartyrelacionado'):
                query += f" AND destipclasifpartyrelacionado IN ({','.join(['?' for _ in filtros['destipclasifpartyrelacionado']])})"
                params.extend(filtros['destipclasifpartyrelacionado'])
            
            if filtros.get('nbrmonedadestino'):
                query += f" AND nbrmonedadestino IN ({','.join(['?' for _ in filtros['nbrmonedadestino']])})"
                params.extend(filtros['nbrmonedadestino'])
            
            if filtros.get('descanal'):
                query += f" AND descanal IN ({','.join(['?' for _ in filtros['descanal']])})"
                params.extend(filtros['descanal'])
            
            if filtros.get('efectivo_only'):
                query += " AND desorigendinero IS NOT NULL AND desorigendinero != ''"
            
            if filtros.get('segmento'):
                query += f" AND SEGMENTO IN ({','.join(['?' for _ in filtros['segmento']])})"
                params.extend(filtros['segmento'])
            
            if filtros.get('destipopereportesbs'):
                query += f" AND destipopereportesbs IN ({','.join(['?' for _ in filtros['destipopereportesbs']])})"
                params.extend(filtros['destipopereportesbs'])
        
        return query, params

    def get_todas_operaciones(self, filtros=None):
        conn = self.get_connection()
        
        query = "SELECT * FROM operaciones WHERE 1=1"
        params = []
        
        query, params = self._aplicar_filtros_sql(query, params, filtros)
        
        try:
            df = pd.read_sql(query, conn, params=params)
        except Exception as e:
            print(f"Error executing query: {e}")
            df = pd.DataFrame()
        finally:
            conn.close()
            
        return df
    
    def get_operaciones_caso(self, id_caso, filtros=None):
        conn = self.get_connection()
        
        clientes_df = pd.read_sql("SELECT DISTINCT CODUNICOCLI_13_enc FROM caso_clientes WHERE id_caso = ?", conn, params=(id_caso,))
        clientes = clientes_df['CODUNICOCLI_13_enc'].tolist()
        
        cargas_df = pd.read_sql("SELECT DISTINCT id_carga FROM caso_cargas WHERE id_caso = ?", conn, params=(id_caso,))
        cargas = cargas_df['id_carga'].tolist()
        
        where_clauses = []
        params = []
        
        if clientes:
            placeholders = ','.join(['?' for _ in clientes])
            where_clauses.append(f"CODUNICOCLI_13_enc IN ({placeholders})")
            params.extend(clientes)
        
        if cargas:
            placeholders = ','.join(['?' for _ in cargas])
            where_clauses.append(f"id_carga IN ({placeholders})")
            params.extend(cargas)
        
        if not where_clauses:
            conn.close()
            return pd.DataFrame()
        
        query = f"SELECT * FROM operaciones WHERE ({' OR '.join(where_clauses)})"
        
        query, params = self._aplicar_filtros_sql(query, params, filtros)
        
        try:
            df = pd.read_sql(query, conn, params=params)
        except:
            df = pd.DataFrame()
        finally:
            conn.close()
            
        return df