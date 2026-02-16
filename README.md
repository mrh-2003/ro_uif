# Sistema de Análisis UIF - Lavado de Activos

Sistema completo de análisis de operaciones bancarias para detección de patrones sospechosos de lavado de activos.

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Crear la base de datos:
```bash
python create_database.py
```

3. Ejecutar la aplicación:
```bash
streamlit run app_complete.py
```

## Estructura del Sistema

- `create_database.py`: Script para crear la base de datos SQLite
- `db_manager.py`: Gestión de base de datos
- `analizador.py`: Módulo de análisis con todos los reportes
- `visualizador.py`: Gráficos interactivos
- `generador_informe.py`: Generación de informes PDF
- `app_complete.py`: Aplicación principal Streamlit

## Funcionalidades

### 1. Carga de Datos
- Cargar archivos Excel con operaciones bancarias
- Validación y formateo automático de datos
- Asignación de código de carga para agrupación

### 2. Gestión de Casos
- Crear casos por clientes específicos
- Crear casos por código de carga
- Visualizar y eliminar casos existentes

### 3. Análisis (18 Reportes)
- Top 10 por columnas relevantes
- Post transferencia internacional
- Ejecutantes, ordenantes y beneficiarios comunes
- Rankings por actores
- Porcentaje de efectivo
- Cuentas comunes
- Operaciones simultáneas
- Ranking de operaciones
- Actividades económicas
- Actividades de riesgo
- Ranking de agencias

### 4. Filtros Generales
- Moneda (SOL/DOLAR/AMBAS)
- Tipo de documento (DNI/RUC/AMBOS)
- Rango de montos
- Rango de fechas
- Tipo de cliente
- Tipo de relación
- Canal
- Segmento
- Tipo de operación
- Solo efectivo

### 5. Visualizaciones
- Gráficos de barras interactivos
- Gráficos de pastel
- Grafos de red (networkx + pyvis)
- Scatter plots
- Gráficos de línea temporal

### 6. Exportación
- Exportar tablas a Excel
- Generar informes PDF completos
- Copiar gráficos fácilmente

## Reportes Disponibles

1. Top 10 de columnas relevantes
2. Ranking post transferencia internacional
3. Ejecutantes comunes entre clientes
4. Ordenantes comunes entre clientes
5. Beneficiarios comunes entre clientes
6. Ranking de ejecutantes más comunes
7. Ranking de ordenantes más comunes
8. Ranking de beneficiarios más comunes
9. Porcentaje de efectivo por cliente
10. Cuentas ordenantes comunes
11. Cuentas beneficiarias comunes
12. Operaciones simultáneas
13. Ranking de tipos de operaciones
14. Actividad económica ejecutantes
15. Actividad económica ordenantes
16. Actividad económica beneficiarios
17. Actividades de riesgo (dragas, seguridad, transporte)
18. Ranking de agencias

## Uso Básico

1. **Cargar Datos**: Subir archivo Excel con las operaciones
2. **Crear Caso**: Agrupar clientes o cargas para análisis
3. **Aplicar Filtros**: Usar sidebar para filtrar datos
4. **Ejecutar Análisis**: Seleccionar tipo de análisis y ejecutar
5. **Exportar**: Descargar Excel o generar PDF

## Características Técnicas

- Base de datos SQLite con índices optimizados
- Gráficos interactivos con Plotly
- Grafos de red con zoom y búsqueda
- Informes PDF profesionales con ReportLab
- Interface responsive con Streamlit
- Persistencia de casos y configuraciones
