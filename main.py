from fastapi import FastAPI
from pydantic import BaseModel
import re
from typing import Optional
import os
import uvicorn

app = FastAPI(title="Factura Parser API")


class ParseRequest(BaseModel):
    text: str


def _search(pattern: str, text: str, flags=0):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _to_float_es(value: Optional[str]):
    if not value:
        return None
    value = value.replace("€", "").replace(" ", "").strip()
    value = value.replace(".", "").replace(",", ".")
    try:
        return float(value)
    except:
        return None


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


@app.post("/parse-iberdrola")
def parse_iberdrola(req: ParseRequest):
    t = req.text

    proveedor = "IBERDROLA CLIENTES, S.A.U." if "IBERDROLA CLIENTES" in t.upper() else None
    tipo_documento = "FACTURA DE ELECTRICIDAD" if "FACTURA DE ELECTRICIDAD" in t.upper() else None

    numero_factura = _search(r"Número de factura\s+([0-9]+)", t, flags=re.IGNORECASE)
    fecha_emision = _search(r"Fecha de emisión de factura\s+(.+)", t, flags=re.IGNORECASE)
    fecha_cargo = _search(r"Fecha prevista de cargo\s+([0-9/]+)", t, flags=re.IGNORECASE)
    periodo_desde = _search(r"Periodo de facturación\s+([0-9/]+)\s*-\s*[0-9/]+", t, flags=re.IGNORECASE)
    periodo_hasta = _search(r"Periodo de facturación\s+[0-9/]+\s*-\s*([0-9/]+)", t, flags=re.IGNORECASE)

    titular = _search(r"Titular\s+(.+)", t, flags=re.IGNORECASE)
    cif_titular = _search(r"CIF titular\s+([A-Z0-9]+)", t, flags=re.IGNORECASE)
    referencia_contrato = _search(r"Referencia contrato suministro[:\s]+([0-9]+)", t, flags=re.IGNORECASE)
    cups = _search(r"Identificación punto de suministro \(CUPS\):\s*(ES[ A-Z0-9]+)", t, flags=re.IGNORECASE)
    direccion_suministro = _search(r"Dirección de suministro:\s*(.+)", t, flags=re.IGNORECASE)

    energia_total_eur = _to_float_es(_search(r"TOTAL ENERGÍA\s+([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))
    servicios_otros_eur = _to_float_es(_search(r"TOTAL SERVICIOS Y OTROS CONCEPTOS\s+([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))
    base_imponible_eur = _to_float_es(_search(r"IMPORTE TOTAL\s+([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))
    iva_eur = _to_float_es(_search(r"IVA\s+21%\s+s/[0-9\.,]+\s+€?\s*([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))
    total_factura_eur = _to_float_es(_search(r"TOTAL IMPORTE FACTURA[:\s]+([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))

    kwh_total = _to_float_es(_search(r"Total\s+([0-9\.,]+)\s*kWh", t, flags=re.IGNORECASE))
    potencia_total_eur = _to_float_es(_search(r"Total importe potencia hasta\s+[0-9/]+\s+([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))
    exceso_potencia_eur = _to_float_es(_search(r"Exceso de potencia\s+([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))
    impuesto_electricidad_eur = _to_float_es(_search(r"Impuesto sobre electricidad.*?\s([0-9\.,]+)\s*€", t, flags=re.IGNORECASE))

    return {
        "proveedor": proveedor,
        "tipo_documento": tipo_documento,
        "numero_factura": numero_factura,
        "fecha_emision": fecha_emision,
        "fecha_cargo": fecha_cargo,
        "periodo_desde": periodo_desde,
        "periodo_hasta": periodo_hasta,
        "titular": titular,
        "cif_titular": cif_titular,
        "referencia_contrato": referencia_contrato,
        "cups": cups,
        "direccion_suministro": direccion_suministro,
        "potencia_total_eur": potencia_total_eur,
        "kwh_total": kwh_total,
        "exceso_potencia_eur": exceso_potencia_eur,
        "impuesto_electricidad_eur": impuesto_electricidad_eur,
        "energia_total_eur": energia_total_eur,
        "servicios_otros_eur": servicios_otros_eur,
        "base_imponible_eur": base_imponible_eur,
        "iva_eur": iva_eur,
        "total_factura_eur": total_factura_eur
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
