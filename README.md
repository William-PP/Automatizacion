# Generador de Anexo 210

Genera el Anexo 210 (declaración de renta) a partir de la exógena DIAN.
Lee el reporte `Reporte` del `.xlsx` de exógena, clasifica cada concepto contra
las reglas de mapeo y escribe el anexo con la plantilla oficial congelada.

## Requisitos

- Python 3.9 o superior
- Una dependencia: `openpyxl`
- `tkinter` (viene con Python en Windows y macOS; en Linux: `python3-tk`)

## Instalación

```bash
py -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
py -m pip install -r requirements.txt
```

## Uso

Interfaz gráfica (recomendado):

```bash
py interfaz_anexo.pyw
```

Línea de comandos:

```bash
py generar_anexo.py                                  # detecta la exógena más reciente
py generar_anexo.py "2025 Exogena ... .xlsx"          # archivo específico
py generar_anexo.py "exogena.xlsx" --salida "anexo.xlsx"
```

### Opciones

| Opción | Efecto |
| --- | --- |
| `--venta-activos-mas2` | La venta de activos fijos poseída más de 2 años va a ganancia ocasional. Por defecto va a rentas no laborales. |
| `--subcontrato-2-mas` | Honorarios, comisiones y servicios (5002/5003/5004) van a renta no laboral en vez de renta de trabajo, porque se subcontrató 2 o más personas por 90 días o más. Sin este flag van a renta de trabajo. |

Ambos existen como checkbox en la interfaz gráfica.

## Cómo se clasifican los conceptos

Cada regla (`generador_anexo/config/reglas_anexo.py`) puede combinar tres
condiciones, todas obligatorias:

- `match_codigo`: código de concepto de la exógena (`1476`, `1315`, `5002`…).
  Es la clave estable con la DIAN, así que ancla la regla aunque cambie el
  texto.
- `match_c`: texto del detalle.
- `match_e`: código de uso de la declaración.

> **Ojo:** el código **no reemplaza** al texto, se combinan. Un mismo código
> puede traer varios conceptos distintos — el `4070` es tanto "Retención
> distribuida" (R132) como "Ingreso distribuido" (R74). Además, los códigos de
> la cédula general **no coinciden** con los de la exógena: en la cédula el
> `2204` es "préstamos bancarios", pero en la exógena el `2204` es "Activos /
> Impuestos, gravámenes y tasas". Por eso `match_codigo` siempre va acompañado
> de `match_c` o `match_e`.

## Filas dinámicas por bloque

El modelo oficial no tiene un número fijo de filas por concepto: son bloques.
Cada bloque abre con una fila de **título** (tiene etiqueta en la columna A) y
sigue con N filas de **detalle** (columna A vacía).

Una regla puede declarar `bloque = <fila del título>` en vez de una fila fija.
Con eso la regla recibe sus filas dentro del bloque, en cascada, y
`infrastructure/excel/planificador.py` inserta automáticamente las que falten
justo antes del siguiente título. No hay que duplicar filas a mano en el
modelo.

Las reglas sin `bloque` conservan el comportamiento anterior: arrancan en
`fila` e insertan el excedente en `fila + max_filas`.

## Estructura

```
generador_anexo/
  config/         datos: reglas de mapeo, plantilla JSON, settings
  domain/         entidades y reglas (sin Excel)
  application/    caso de uso: orquesta leer -> mapear -> escribir
  infrastructure/ excel: lector, escritor, planificador, totales
  presentation/   CLI y GUI
```

Capas: `presentation` → `application` → `domain`, e `infrastructure` resuelve
el detalle de Excel.

## La plantilla

`generador_anexo/config/anexo_layout.json` es una descripción congelada de
toda la hoja `Borrador 210` del modelo oficial: celdas, estilos, merges, anchos
de columna, alturas de fila y paginación.

**El generador no lee el `.xlsx` del modelo en runtime.** Si necesitas
actualizar la plantilla tras un cambio de la DIAN, regenera el JSON desde el
`.xlsx` nuevo y commitéalo.

## Datos sensibles

Las exógenas (`*Exogena*.xlsx`) y los anexos generados contienen información
tributaria de terceros. Están en `.gitignore` y **no deben subirse al
repositorio**. Para probar, usa exógenas de pruebas anonimizadas.
