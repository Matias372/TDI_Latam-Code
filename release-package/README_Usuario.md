# 📋 README.md para GitHub

```markdown
# 🚀 SyncDesk Manager

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Estado-Producción%20Ready-success.svg)]()

**SyncDesk Manager** - Sistema integral para la gestión y sincronización de tickets entre **Freshdesk** y **Clarity**, diseñado para optimizar flujos de trabajo y mantener consistencia entre sistemas.

## ✨ Características Principales

### 🔄 Sincronización Inteligente
- **Sincronización bidireccional** de estados entre Freshdesk y Clarity
- **Mapeo automático** de estados entre sistemas
- **Procesamiento por lotes** para grandes volúmenes de tickets
- **Verificación de estructura** de archivos antes de procesar

### 📊 Sistema de Reportes Avanzado
- **📋 Tickets sin etiquetas** - Identificación de tickets sin categorizar
- **🏢 Lista de empresas** - Directorio completo de empresas en Freshdesk
- **🔄 Productos diferentes** - Detección de discrepancias en productos entre sistemas
- **Descarga automática** en formato Excel a carpeta de Descargas

### ⚙️ Procesos Automatizados
- **📨 Envío de notas internas** a tickets inactivos (>10 días)
- **Gestión dinámica de agentes** - Se agregan automáticamente al detectarlos
- **Modo manual/automático** para control granular de procesos
- **Detección inteligente** de inactividad y tickets prioritarios

### 📚 Experiencia de Usuario Premium
- **Interfaz intuitiva** con menús navegables y emojis
- **Barras de progreso** en tiempo real para procesos largos
- **Guía de usuario integrada** con 7 secciones completas
- **Confirmaciones** para operaciones críticas

## 🛠️ Requisitos del Sistema

### Requisitos Mínimos
- **Sistema Operativo**: Windows 10/11, macOS 10.14+, Ubuntu 18.04+
- **Python**: Versión 3.8 o superior
- **Memoria RAM**: 4 GB mínimo
- **Espacio disco**: 500 MB libres

### Dependencias Python
```bash
requests==2.31.0
pandas==2.0.3
openpyxl==3.1.2
python-dateutil==2.8.2
pytz==2023.3
```

## 🚀 Instalación Rápida

### Método 1: Ejecutable (Recomendado para usuarios finales)
1. **Descargar** la última release desde [Releases](https://github.com/Matias372/TDI_Latam-Code.git/releases)
2. **Extraer** el archivo ZIP en la carpeta deseada
3. **Ejecutar** `SyncDeskManager.exe`
4. **Configurar** conexiones en el primer inicio

### Método 2: Código Fuente (Para desarrolladores)
```bash
# Clonar repositorio
git clone https://github.com/Matias372/TDI_Latam-Code.git
cd freshdesk-system

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python run.py
```

## ⚙️ Configuración Inicial

### 1. Configurar Freshdesk
```
🌐 Dominio: https://tu-empresa.freshdesk.com
🔑 API Key: Obtener desde https://tu-empresa.freshdesk.com/admin/apikey
```

### 2. Configurar Clarity
```
🌐 Dominio: https://pmservice.empresa.com:puerto/ppm/rest/v1
👤 Usuario: Tu usuario de Clarity
🔐 Contraseña: Tu contraseña de Clarity
```

### 3. Formatos de Archivo Requeridos

#### 📊 Archivos Freshdesk (Excel)
- **Tipo 1**: Reporte de Tickets sin Actividad (para envío de notas)
- **Tipo 2**: Lista Completa de Tickets (para sincronización)

#### 📄 Archivo Clarity (CSV)
- **Formato específico**: Exportación directa de Clarity sin modificaciones
- **Estructura**: Texto con comillas, separado por comas, dos encabezados

## 🎯 Guía Rápida de Uso

### Flujo de Sincronización
```
1. Exportar tickets desde Freshdesk (Excel - Tipo 2)
2. Exportar datos desde Clarity (CSV - Formato nativo)
3. Ejecutar: Menú Principal → Procesos → Sincronizar estados
4. Revisar diferencias y confirmar cambios
5. Sistema aplica actualizaciones automáticamente
```

### Flujo de Reportes
```
1. Menú Principal → Reportes → Seleccionar reporte deseado
2. Seguir instrucciones específicas para cada reporte
3. Los archivos se guardan automáticamente en Descargas
```

## 📁 Estructura del Proyecto

```
freshdesk-system/
├── src/                          # Código fuente
│   ├── config/                  # Gestión de configuración
│   ├── features/               # Lógica de negocio principal
│   ├── services/               # Clientes de API (Freshdesk, Clarity)
│   ├── utils/                  # Utilidades y helpers
│   └── menus/                  # Sistema de menús interactivos
├── data/                       # Datos y configuración
│   ├── config/                # Archivos de configuración
│   ├── templates/             # Plantillas Excel
│   └── output/                # Archivos generados
├── logs/                      # Registros del sistema (rotación 30 días)
└── docs/                      # Documentación adicional
```

## 🔧 Desarrollo y Contribuciones

### Estructura del Código
```python
# Arquitectura modular y mantenible
from src.main import main
from src.services.freshdesk_service import FreshdeskService
from src.features.sync_processes import SyncProcess
```

### Ejecutar en modo desarrollo
```bash
# Instalar en modo desarrollo
pip install -e .

# Ejecutar tests (si existen)
python -m pytest tests/

# Verificar cobertura de código
python -m pytest --cov=src tests/
```

## 🐛 Soporte Técnico

### Solución de Problemas Comunes
- **Verificar logs** en carpeta `logs/` junto al ejecutable
- **Confirmar formatos** de archivo según la guía integrada
- **Validar conexión** a internet y credenciales

### Contactar Soporte
- **📧 Email**: matiasruibal372@gmail.com
- **📝 Asunto**: `🚨 INCIDENTE SyncDesk Manager - Asistencia Urgente Requerida`

**Incluir en el mensaje:**
1. Mensaje de error completo
2. Pasos realizados antes del error
3. Operación específica intentada
4. Archivos de log relevantes

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 🏆 Changelog

### v1.0.0 - Versión Inicial
- ✅ Sincronización completa Freshdesk ↔ Clarity
- ✅ Sistema de reportes avanzado
- ✅ Guía de usuario integrada
- ✅ Interfaz intuitiva con menús
- ✅ Logs con rotación automática
- ✅ Preparado para distribución

---

**¿Preguntas?** Revisa la guía de usuario integrada en la aplicación o contacta al soporte técnico.

⭐ **Si este proyecto te resulta útil, por favor dale una estrella en GitHub!**
```
