# ⚡ WinCleaner

**WinCleaner** es una herramienta de limpieza para Windows con interfaz gráfica (`tkinter`) diseñada para liberar espacio en disco de forma rápida, segura y sencilla.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)

---

# ✨ Características

- 🗂 **Limpieza de archivos temporales**
  - `%LOCALAPPDATA%\Temp`
  - `%TEMP%`
  - `C:\Windows\Temp`

- 🗑 **Vaciar papelera de reciclaje**

- ⚡ **Limpieza de Prefetch**
  - `C:\Windows\Prefetch`

- 📋 **Limpieza de logs del sistema**
  - `C:\Windows\Logs`
  - `C:\Windows\inf`

- 💾 **Análisis de disco**
  - Visualiza el uso del disco
  - Detecta carpetas pesadas

- ☑️ **Módulos configurables**
  - Activa/desactiva cada limpieza individualmente

- 🔒 **Elevación automática de administrador**

- 📝 **Log en tiempo real**
  - Muestra archivos eliminados y errores omitidos

---

# 🖥 Interfaz

| Pestaña | Descripción |
|---|---|
| 🧹 Limpiar | Ejecuta la limpieza seleccionando módulos |
| 💾 Disco | Analiza el espacio ocupado del disco |

---

# 🚀 Instalación y uso

## Opción 1 — Ejecutar desde Python

### Requisitos

- Windows 10 / 11
- Python 3.10 o superior
- `tkinter` incluido en Python

### Ejecutar

```bash
git clone https://github.com/TUUSUARIO/WinCleaner.git
cd WinCleaner

python cleaner.py
```

---

## Opción 2 — Crear el `.exe`

### Instalar dependencias

```bash
pip install pyinstaller
```

### Compilar

```bash
pyinstaller --onefile --windowed --icon=icon.ico cleaner.py
```

El ejecutable se generará en:

```txt
dist/cleaner.exe
```

---

## Opción 3 — Compilar automáticamente con `.bat`

El proyecto incluye un script `.bat` para generar el ejecutable automáticamente.

### Ejecutar

```txt
build.bat
```

El `.exe` aparecerá en:

```txt
dist/
```

---

# ⚙️ ¿Qué limpia exactamente?

| Módulo | Rutas |
|---|---|
| Temporales | `%LOCALAPPDATA%\Temp`, `%TEMP%`, `C:\Windows\Temp` |
| Prefetch | `C:\Windows\Prefetch` |
| Logs | `C:\Windows\Logs`, `C:\Windows\inf` |
| Papelera | Papelera del sistema |

> Los archivos en uso o bloqueados se omiten automáticamente sin detener la limpieza.

---

# 🔐 Permisos

WinCleaner solicita permisos de administrador automáticamente al iniciarse para poder acceder a carpetas protegidas del sistema.

Si se ejecuta sin permisos de administrador, algunas funciones estarán limitadas.

---

# 📂 Estructura del proyecto

```txt
WinCleaner/
│
├── cleaner.py
├── build.bat
├── icon.ico
├── README.md
├── requirements.txt
│
├── dist/
├── build/
└── __pycache__/
```

---