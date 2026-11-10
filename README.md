# 👁 Ojo Hermano

> *"I am always watching."* 

**Ojo Hermano** es una aplicación de escritorio para Windows que monitorea el hardware de tu PC en tiempo real, diseñada especialmente para detectar y diagnosticar crashes de GPU durante sesiones de juego.

---

## ¿Por qué Ojo Hermano?

Inspirado en **Brother Eye** — la IA de vigilancia de Batman — esta app monitorea silenciosamente tu PC, detecta automáticamente cuando el driver de video se cuelga (TDR), y registra el estado exacto del hardware en ese instante.

---

## Features (Fase 1)

- 🌡️ **Gauges circulares en tiempo real** — GPU Temp, GPU Load, CPU, RAM
- 📊 **Gráfico histórico** — últimos 15 minutos de todas las métricas
- 🖥️ **CPU Cores individuales** — carga por thread (i7-4790: 8 threads)
- 🌐 **Red** — velocidad de descarga/subida en tiempo real
- ⚡ **Detector automático de TDR** — registra cada crash de driver AMD con snapshot de hardware
- 🔔 **Notificaciones nativas de Windows** — alerta cuando hay crash o temperatura crítica
- 🔽 **System Tray** — corre en background, siempre vigilando
- 🎮 **Overlay HUD** — `Ctrl+Shift+O` para mostrar/ocultar métricas sobre el juego (próximamente)

---

## Stack

| Componente | Tecnología |
|---|---|
| UI | Python + PyQt6 |
| Sensores | LibreHardwareMonitor (via pythonnet) |
| Event Log | PowerShell (subprocess) |
| Hotkeys | `keyboard` library |
| Persistencia | CSV + JSON |

---

## Hardware soportado

Desarrollado y probado en:
- **CPU**: Intel Core i7-4790
- **GPU**: AMD Radeon R9 390 Series
- **OS**: Windows 10

Compatible con cualquier CPU Intel/AMD y GPU AMD/Nvidia soportada por LibreHardwareMonitor.

---

## Instalación

### Requisitos

- Python 3.12+
- Windows 10/11

### Setup

```bash
git clone https://github.com/DiVilota/ojo-hermano.git
cd ojo-hermano
pip install -r requirements.txt
```

Descarga [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) y coloca `LibreHardwareMonitorLib.dll` en la carpeta del proyecto (o ajusta la ruta en `core/monitor.py`).

### Correr

```bash
python main.py
```

> **Nota**: Para leer temperaturas de CPU, ejecutar como Administrador.

---

## Estructura

```
ojo-hermano/
├── main.py                  # Entry point
├── core/
│   ├── monitor.py           # Polling de LibreHardwareMonitor (QThread)
│   ├── watchdog.py          # Detector de crashes TDR (QThread)
│   └── data_store.py        # Buffer circular + persistencia CSV
├── ui/
│   ├── main_window.py       # Ventana principal
│   ├── overlay.py           # HUD transparente sobre juegos
│   ├── tray.py              # System tray icon
│   └── widgets/
│       ├── gauge.py         # Widget gauge circular
│       └── sparkline.py     # Gráfico de líneas multi-serie
└── assets/
```

---

## Roadmap

- [x] **Fase 1** — Monitor base + system tray + detección TDR
- [ ] **Fase 2** — Overlay HUD sobre juego + sesión gaming tracker
- [ ] **Fase 3** — Análisis predictivo + historial de sesiones

---

## Licencia

MIT
