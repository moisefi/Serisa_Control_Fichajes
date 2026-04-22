from __future__ import annotations

from datetime import datetime

from servicios.servicio_exportacion import ExportadorExcel, ExportadorPDF


def _filas_demo():
    return [
        (1, "Ana Ruiz", "UID-001", datetime(2026, 4, 1, 8, 0, 0), "entrada"),
        (2, "Ana Ruiz", "UID-001", datetime(2026, 4, 1, 17, 0, 0), "salida"),
    ]


def test_exportador_excel_genera_archivo(tmp_path):
    ruta = tmp_path / "reporte.xlsx"
    ExportadorExcel.exportar(str(ruta), _filas_demo())
    assert ruta.exists()
    assert ruta.stat().st_size > 0


def test_exportador_pdf_genera_archivo(tmp_path):
    ruta = tmp_path / "reporte.pdf"
    ExportadorPDF.exportar(str(ruta), _filas_demo(), filtros_texto="usuario=Ana Ruiz")
    assert ruta.exists()
    assert ruta.stat().st_size > 0

