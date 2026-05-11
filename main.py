from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import re

app = FastAPI(title="Factura Parser API")

class ParseRequest(BaseModel):
    text: str

def _search(pattern: str, text: str, flags=0):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None

@app.get("/")
def root():
    return {"ok": True, "service": "factura-parser"}

@app.post("/parse")
def parse_invoice(req: ParseRequest):
    t = req.text

    cliente = _search(r"Cliente:\s*(.+?)\s*CUPS:", t, flags=re.DOTALL)
    cups = _search(r"CUPS:\s*([A-Z0-9]+)", t)
    cif = _search(r"CIF:\s*([A-Z0-9]+)", t)

    fecha_factura = _search(r"Fecha de factura:\s*([0-9./-]+)", t)
    fecha_inicio = _search(r"Fecha Inicio:\s*([0-9./-]+)", t)
    fecha_fin = _search(r"Fecha Fin:\s*([0-9./-]+)", t)

    tarifa_acceso = _search(r"Tarifa de Acceso:\s*([0-9A-Z.]+)", t)
    atr_directo = _search(r"ATR Directo:\s*(SI|NO)", t)
    numero_factura = _search(r"Número de factura:\s*([A-Z0-9-]+)", t)

    kwh_simulados_str = _search(r"CIF:.*?([0-9.]+)\s*kWh", t, flags=re.DOTALL)
    kwh_simulados = float(kwh_simulados_str.replace(".", "").replace(",", ".")) if kwh_simulados_str else None

    coste_str = _search(r"COSTE TOTAL SIMULACIÓN.*?([0-9\.,]+)\s*€", t, flags=re.DOTALL)
    coste_total_simulacion = float(coste_str.replace(".", "").replace(",", ".")) if coste_str else None

    return {
        "cliente": cliente,
        "cups": cups,
        "cif": cif,
        "fecha_factura": fecha_factura,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "numero_factura": numero_factura,
        "kwh_simulados": kwh_simulados,
        "coste_total_simulacion": coste_total_simulacion,
        "tarifa_acceso": tarifa_acceso,
        "atr_directo": atr_directo
    }
