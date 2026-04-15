from __future__ import annotations

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ExportadorExcel:
    @staticmethod
    def exportar(ruta: str, filas: list[tuple]) -> None:
        dataframe = pd.DataFrame(filas, columns=["ID", "Usuario", "UID", "FechaHora", "Tipo"])
        dataframe = dataframe.drop(columns=["ID"])
        dataframe = dataframe.rename(columns={"UID": "Tarjeta"})
        dataframe.to_excel(ruta, index=False)


class ExportadorPDF:
    @staticmethod
    def exportar(ruta: str, filas: list[tuple], filtros_texto: str = "") -> None:
        documento = SimpleDocTemplate(
            ruta,
            pagesize=landscape(A4),
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        estilos = getSampleStyleSheet()

        estilo_titulo = ParagraphStyle(
            name="TituloInforme",
            parent=estilos["Title"],
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            fontSize=20,
            spaceAfter=18,
            textColor=colors.black,
        )

        estilo_filtro_titulo = ParagraphStyle(
            name="FiltroTitulo",
            parent=estilos["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        )

        estilo_filtro_texto = ParagraphStyle(
            name="FiltroTexto",
            parent=estilos["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT,
        )

        elementos = [
            Paragraph("Informe de registros", estilo_titulo),
            Spacer(1, 8),
        ]

        if filtros_texto:
            tabla_filtros = Table(
                [
                    [Paragraph("Filtros aplicados", estilo_filtro_titulo)],
                    [Paragraph(filtros_texto, estilo_filtro_texto)],
                ],
                colWidths=[320],
            )
            tabla_filtros.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3B4D")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4F6F8")),
                        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#A0A0A0")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D0D0")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            elementos.extend([tabla_filtros, Spacer(1, 16)])

        datos = [["Usuario", "Tarjeta", "Fecha/Hora", "Tipo"]]
        datos.extend([
            [
                str(fila[1]),
                str(fila[2]),
                fila[3].strftime("%Y-%m-%d %H:%M:%S") if fila[3] else "",
                str(fila[4]),
            ]
            for fila in filas
        ])

        tabla = Table(
            datos,
            repeatRows=1,
            colWidths=[110, 110, 190, 70],
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3B4D")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elementos.append(tabla)
        documento.build(elementos)
