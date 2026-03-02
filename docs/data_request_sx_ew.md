# Variables principales a solicitar — Etapa SX y EW (solo las que NO estén ya solicitadas en tu data request base)

> Este archivo es una **lista base**. Ajustar nombres exactos según tags/historians.

## SX (Solvent Extraction)
### Hidráulica y operación de mixer-settlers
- Caudal **PLS a SX** por tren (m³/h) + total
- Caudal **refino a lixiviación** (m³/h) por tren
- Caudal **orgánico** (m³/h) por tren (si disponible)
- Temperaturas (PLS, orgánico, mezclador) por tren
- Nivel de fases en settlers (orgánico / acuoso) y/o alarmas de interface
- Densidad o conductividad (si hay) para detectar arrastres / desbalances

### Química / metalurgia de SX
- Cu (g/L) en: PLS feed, raffinate, electrolyte rich, electrolyte lean (por tren si existe)
- H2SO4 (g/L) en: PLS feed, raffinate, ER, EL
- Impurezas relevantes (g/L): Cl, Fe total, Fe2+/Fe3+, Mn, Al, Mg (según disponibilidad)
- Parámetros de control: O/A ratio, setpoints de flujo, válvulas relevantes

### Performance / calidad
- Transferencia Cu por tren (t Cu/d) si existe cálculo en DCS/PI
- Eficiencia SX / extracción (%), pérdidas a raffinate, arrastre orgánico (proxy)
- Consumo de reactivos SX (extractante, diluyente, modificador) si aplica (L/d o kg/d)

## EW (Electrowinning)
### Producción y operación
- Producción de cátodos (t Cu/d) y por turno
- Corriente total (kA) y por celda (si aplica)
- Voltaje promedio (V) y energía específica (kWh/t Cu)
- Disponibilidad de celdas / celdas en mantención / fallas

### Química electrolito
- Cu (g/L) en electrolito rico y pobre
- H2SO4 (g/L) en electrolito rico y pobre
- Impurezas (g/L o ppm): Cl, Mn, Fe, Co, Ni, As, Sb, Bi (según control)
- Temperatura electrolito (°C)

### Inventarios / balances
- Inventario electrolito (m³) y niveles de estanques
- Purgas/bleed (m³/h) y make-up (m³/h)
- Adiciones de ácido (t/d) y agua (m³/h) a electrolito

## Metadatos (críticos para auditoría)
- Zona horaria, calendarios de turno, cambios de tag, historial de calibración de instrumentos críticos
