# Radar Chile–Bolivia · Modo test
**L3B · Logistic Living Lab** · www.l3b.cl

Piloto del radar de alerta temprana. Cruza plano (BAPLIE), manifiesto, bookings, registro de terminal y listado de vacíos, y marca los contenedores calientes con su porqué.

**Todos los datos son simulados** (naves, clientes, BL, sellos y contenedores ficticios).

- `app.py`: tablero Streamlit
- `motor.py`: generador de documentos ficticios y motor de cruce
- `gestion.py`: capa de gestión de alertas (estado, responsable, coordinación con Aduana, comentario e historial)
- `requirements.txt`: librerías
- `.streamlit/config.toml`: colores L3B

## Gestión y seguimiento (demo)

- **Lista caliente y ficha**: cada alerta tiene estado (Nuevo · En revisión MSC · Coordinado con Aduana · Cerrado con/sin hallazgo), responsable, fecha de coordinación con Aduana, comentario e historial. Botón «Tomar este caso».
- **Mi gestión**: casos por usuario o equipo (Norte, Centro, Biobío), en seguimiento o cerrados.
- **Seguimiento semanal**: rojos detectados, coordinados con Aduana, cerrados y tasa de hallazgo, con texto listo para el reporte y descarga en Excel.
- **¿Por qué este color?**: la ficha muestra la suma de puntos que lleva al semáforo.

En la demo la gestión vive en memoria del servidor: se comparte entre los usuarios conectados, parte con una semana simulada de trabajo y se pierde al reiniciar la app (botón «Reiniciar gestión de la demo»). En la implementación real va a una base de datos.
