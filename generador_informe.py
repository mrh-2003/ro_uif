from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import io

class GeneradorInforme:
    def __init__(self, nombre_caso, descripcion=""):
        self.nombre_caso = nombre_caso
        self.descripcion = descripcion
        self.elementos = []
        self.styles = getSampleStyleSheet()
        
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
    
    def agregar_portada(self):
        titulo = Paragraph(f"<b>INFORME DE ANÁLISIS UIF</b>", self.styles['CustomTitle'])
        self.elementos.append(titulo)
        self.elementos.append(Spacer(1, 0.5*inch))
        
        caso = Paragraph(f"<b>Caso:</b> {self.nombre_caso}", self.styles['CustomHeading'])
        self.elementos.append(caso)
        self.elementos.append(Spacer(1, 0.2*inch))
        
        if self.descripcion:
            desc = Paragraph(f"<b>Descripción:</b> {self.descripcion}", self.styles['CustomBody'])
            self.elementos.append(desc)
            self.elementos.append(Spacer(1, 0.2*inch))
        
        fecha = Paragraph(f"<b>Fecha de generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                         self.styles['CustomBody'])
        self.elementos.append(fecha)
        self.elementos.append(PageBreak())
    
    def agregar_seccion(self, titulo, contenido):
        self.elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['CustomHeading']))
        self.elementos.append(Spacer(1, 0.1*inch))
        
        if isinstance(contenido, str):
            self.elementos.append(Paragraph(contenido, self.styles['CustomBody']))
        
        self.elementos.append(Spacer(1, 0.2*inch))
    
    def agregar_tabla(self, df, titulo=None, max_rows=20):
        if titulo:
            self.elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['CustomHeading']))
            self.elementos.append(Spacer(1, 0.1*inch))
        
        df_display = df.head(max_rows).copy()
        
        for col in df_display.columns:
            if df_display[col].dtype == 'float64':
                df_display[col] = df_display[col].apply(lambda x: f"{x:,.2f}" if pd.notna(x) else "")
            elif df_display[col].dtype == 'int64':
                df_display[col] = df_display[col].apply(lambda x: f"{x:,}" if pd.notna(x) else "")
        
        data = [df_display.columns.tolist()] + df_display.values.tolist()
        
        col_widths = [min(2*inch, 6*inch / len(df_display.columns)) for _ in df_display.columns]
        
        tabla = Table(data, colWidths=col_widths)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        self.elementos.append(tabla)
        self.elementos.append(Spacer(1, 0.3*inch))
    
    def agregar_estadisticas(self, stats_dict, titulo="Estadísticas Generales"):
        self.elementos.append(Paragraph(f"<b>{titulo}</b>", self.styles['CustomHeading']))
        self.elementos.append(Spacer(1, 0.1*inch))
        
        for key, value in stats_dict.items():
            if isinstance(value, (int, float)):
                if isinstance(value, float):
                    texto = f"• <b>{key}:</b> {value:,.2f}"
                else:
                    texto = f"• <b>{key}:</b> {value:,}"
            else:
                texto = f"• <b>{key}:</b> {value}"
            
            self.elementos.append(Paragraph(texto, self.styles['CustomBody']))
        
        self.elementos.append(Spacer(1, 0.2*inch))
    
    def agregar_hallazgo(self, titulo, descripcion, nivel="INFO"):
        colores = {
            "CRITICO": colors.red,
            "ALTO": colors.orange,
            "MEDIO": colors.yellow,
            "BAJO": colors.lightblue,
            "INFO": colors.lightgreen
        }
        
        color = colores.get(nivel, colors.lightgrey)
        
        data = [[Paragraph(f"<b>[{nivel}] {titulo}</b>", self.styles['CustomBody'])]]
        tabla = Table(data, colWidths=[6*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 2, colors.black)
        ]))
        
        self.elementos.append(tabla)
        self.elementos.append(Spacer(1, 0.05*inch))
        self.elementos.append(Paragraph(descripcion, self.styles['CustomBody']))
        self.elementos.append(Spacer(1, 0.2*inch))
    
    def generar_pdf(self, filename):
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        doc.build(self.elementos)
        return filename
    
    def generar_pdf_bytes(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        doc.build(self.elementos)
        buffer.seek(0)
        return buffer
