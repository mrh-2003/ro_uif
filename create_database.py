import sqlite3
from datetime import datetime

def create_database():
    conn = sqlite3.connect('uif_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cargas (
        id_carga INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_carga TEXT UNIQUE NOT NULL,
        fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        archivo_nombre TEXT,
        total_registros INTEGER
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS operaciones (
        id_operacion INTEGER PRIMARY KEY AUTOINCREMENT,
        id_carga INTEGER,
        CODUNICOCLI_13_enc TEXT,
        TIPO_DE_MARCA TEXT, 
        Delito TEXT,
        DESTIPDOCUMENTO TEXT,
        DESTIPBANCA TEXT,
        SEGMENTO TEXT,
        ACT_ECONOMICA TEXT,
        CODUNICOCLI_13 TEXT,
        busqueda TEXT,
        flgtipoclibusqueda TEXT,
        destipclasifpartyrelacionado TEXT,
        descanal TEXT,
        codigo_ubigeo TEXT,
        fec_operacion DATE,
        hora_operacion TIME,
        tipo_ejecutante TEXT,
        tipo_doc_ejecutante TEXT,
        doc_ejecutante_encriptado TEXT,
        DesOcupSOL TEXT,
        tipo_ordenante TEXT,
        tipo_doc_ordenante TEXT,
        doc_ordenante_encriptado TEXT,
        DesOcupOrd TEXT,
        DepOrd TEXT,
        ProvOrd TEXT,
        DisOrd TEXT,
        tipo_beneficiario TEXT,
        tipo_doc_beneficiario TEXT,
        doc_beneficiario_encriptado TEXT,
        DesOcupBen TEXT,
        DepBen TEXT,
        ProvBen TEXT,
        DisBen TEXT,
        tipopereportesbs TEXT,
        destipopereportesbs TEXT,
        desorigendinero TEXT,
        nbrmonedadestino TEXT,
        mtotrx REAL,
        codcta20ordenante TEXT,
        codcta20beneficiario TEXT,
        FOREIGN KEY (id_carga) REFERENCES cargas(id_carga)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS casos (
        id_caso INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_caso TEXT UNIQUE NOT NULL,
        descripcion TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS caso_clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_caso INTEGER,
        CODUNICOCLI_13_enc TEXT,
        FOREIGN KEY (id_caso) REFERENCES casos(id_caso)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS caso_cargas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_caso INTEGER,
        id_carga INTEGER,
        FOREIGN KEY (id_caso) REFERENCES casos(id_caso),
        FOREIGN KEY (id_carga) REFERENCES cargas(id_carga)
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_operaciones_cliente ON operaciones(CODUNICOCLI_13_enc)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_operaciones_carga ON operaciones(id_carga)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_operaciones_fecha ON operaciones(fec_operacion)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_operaciones_tipo ON operaciones(destipopereportesbs)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ejecutante ON operaciones(doc_ejecutante_encriptado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ordenante ON operaciones(doc_ordenante_encriptado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_beneficiario ON operaciones(doc_beneficiario_encriptado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cta_ordenante ON operaciones(codcta20ordenante)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cta_beneficiario ON operaciones(codcta20beneficiario)')
    
    conn.commit()
    conn.close()
    print("Base de datos creada exitosamente")

if __name__ == "__main__":
    create_database()
