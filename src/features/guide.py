"""
Guía de Usuario del Sistema de Gestión Freshdesk
"""

class UserGuide:
    def __init__(self):
        self.sections = {
            "intro": self.get_introduction(),
            "config": self.get_configuration_guide(),
            "reports": self.get_reports_guide(),
            "processes": self.get_processes_guide(),
            "formats": self.get_file_formats_guide(),
            "sync": self.get_sync_guide(),
            "troubleshoot": self.get_troubleshooting_guide()
        }

    def get_introduction(self):
        return """
╔══════════════════════════════════════════════╗
║             🚀 BIENVENIDO AL SISTEMA        ║
╚══════════════════════════════════════════════╝

📋 DESCRIPCIÓN GENERAL:
   Sistema de Gestión Freshdesk - Versión Local
   Herramienta para sincronizar y gestionar tickets entre Freshdesk y Clarity

🎯 FUNCIONALIDADES PRINCIPALES:
   • 🔄 Sincronización de estados entre Freshdesk y Clarity
   • 📊 Generación de reportes y análisis
   • 📨 Envío automatizado de notas internas
   • 🔍 Monitoreo de tickets inactivos

🏗️  ARQUITECTURA:
   • Freshdesk ←→ Sistema ←→ Clarity
   • Procesamiento por lotes desde archivos Excel/CSV
   • Interfaz de consola amigable con menús intuitivos
"""

    def get_configuration_guide(self):
        return """
╔══════════════════════════════════════════════╗
║             🔧 CONFIGURACIÓN                ║
╚══════════════════════════════════════════════╝

🌐 CONFIGURACIÓN DE FRESHDESK:

📌 API Key de Freshdesk:
   • Obtener desde: https://[tu-dominio].freshdesk.com/admin/apikey
   • La API Key es necesaria para todas las operaciones

📌 Dominio de Freshdesk:
   • Formato: https://[nombre-empresa].freshdesk.com
   • Ejemplo: https://mitienda.freshdesk.com

🔐 CONFIGURACIÓN DE CLARITY:

📌 Credenciales de Clarity:
   • Usuario y contraseña proporcionados por el administrador
   • Mismas credenciales que usas para acceder a Clarity vía web

📌 Dominio de Clarity:
   • Formato automático: https://pmservice.[empresa].com:[puerto]/ppm/rest/v1
   • Ejemplo: https://pmservice.ejemplo.com:1234/ppm/rest/v1

📁 CONFIGURACIÓN POR ARCHIVO TXT:

Puedes crear un archivo config.txt con este formato:

   API_Freshdesk: tu_api_key_aqui
   Freshdesk_domain: https://tudominio.freshdesk.com
   Clarity_user: tu_usuario_clarity
   Clarity_pass: tu_contraseña_clarity
   Clarity_domain: https://pmservice.empresa.com:puerto/ppm/rest/v1
"""

    def get_reports_guide(self):
      return """
   ╔══════════════════════════════════════════════╗
   ║               📊 REPORTES                   ║
   ╚══════════════════════════════════════════════╝

   📋 TICKETS SIN ETIQUETAS:
      • Propósito: Identificar tickets que no tienen etiquetas asignadas
      • Fuente: Consulta directa a la API de Freshdesk
      • Salida: Excel con tickets sin etiquetas y su información básica

   🏢 LISTA DE EMPRESAS:
      • Propósito: Obtener listado completo de empresas en Freshdesk
      • Fuente: API de Freshdesk
      • Salida: Excel con empresas y sus dominios

   🔄 PRODUCTOS DIFERENTES (FRESHDESK vs CLARITY):
      • Propósito: Detectar discrepancias en productos asignados
      • Archivos requeridos:
         - Freshdesk: Lista Completa de Tickets (con columna 'Producto')
         - Clarity: CSV con formato específico (exportación directa de Clarity)
      • Salida: Excel en carpeta Descargas con diferencias encontradas
   """

def get_file_formats_guide(self):
    return """
╔══════════════════════════════════════════════╗
║             📁 FORMATOS DE ARCHIVOS         ║
╚══════════════════════════════════════════════╝

📊 ARCHIVOS FRESHDESK (EXCEL) - DOS TIPOS:

🎯 TIPO 1: REPORTE DE TICKETS SIN ACTIVIDAD
   • Propósito: Envío de notas internas a tickets inactivos
   • Columnas clave requeridas:
      - Ticket ID → Identificador único del ticket

   📋 Columnas típicas en este reporte:
      - Nombre de la empresa
      - Ticket ID
      - Tipo de Ticket
      - Asunto
      - Estado
      - Fecha de creación
      - Seleccione el producto
      - Nombre del agente
      - Nombre del agente interno
      - Prioridad
      - Fecha de última actualización

🎯 TIPO 2: LISTA COMPLETA DE TICKETS (PERIODO 1 AÑO)
   • Propósito: Sincronización de estados con Clarity y reporte de productos diferentes
   • Columnas clave requeridas:
      - Ticket ID → Identificador único del ticket
      - Estado → Estado actual en Freshdesk
      - Producto → Producto actual en Freshdesk

   📋 Columnas típicas en este reporte:
      - Nombre de la empresa
      - Ticket ID
      - Tipo de Ticket
      - Asunto
      - Estado
      - Producto (de segmento - fabricante - producto)
      - Nombre del agente

📄 ARCHIVO CLARITY (CSV - FORMATO ESPECÍFICO):

⚠️  IMPORTANTE: Usar la exportación DIRECTA de Clarity sin modificar el formato

Estructura característica:
   • Formato: Texto con valores entre comillas, separados por comas
   • Dos líneas de encabezado
   • Campos entre comillas dobles

Ejemplo real de las primeras líneas:
   "Cliente","Conversación","Nombre","Nombre","Recursos asignados","Inicio","Finalización","Estado","Producto TDI","ID","Estado Freshdesk"
   "Cliente A","Conversación 1","Nombre 1","Nombre 2","Recursos","2024-01-01","2024-01-02","Abierta","Producto A","12345","Abierta"

Columnas requeridas en el archivo:
   • ID                 → Identificador del ticket (debe coincidir con Ticket ID)
   • Estado Freshdesk   → Estado actual en Clarity  
   • Producto TDI       → Para reporte de productos diferentes

🔧 NOTA TÉCNICA:
   El sistema está diseñado específicamente para leer este formato de Clarity.
   No modifique la estructura del archivo CSV exportado desde Clarity.

👥 ARCHIVO DE AGENTES (EXCEL):

Columnas requeridas:
   • ID     → Identificador del agente en Freshdesk
   • Agente → Nombre del agente
   • MAIL   → Email del agente

Ejemplo:
   ┌───────────┬──────────────┬───────────────────┐
   │    ID     │   Agente     │       MAIL        │
   ├───────────┼──────────────┼───────────────────┤
   │ 820000001 │ Juan Pérez   │ juan@empresa.com  │
   │ 820000002 │ María García │ maria@empresa.com │
   └───────────┴──────────────┴───────────────────┘
"""

def get_processes_guide(self):
    return """
╔══════════════════════════════════════════════╗
║              ⚙️ PROCESOS                    ║
╚══════════════════════════════════════════════╝

📨 REVISAR TICKETS SIN ACTIVIDAD:

📌 Propósito:
   • Enviar notas internas a tickets inactivos por más de 10 días
   • Recordar a agentes sobre tickets pendientes

📌 Archivo Freshdesk requerido:
   • TIPO: Reporte de Tickets sin Actividad
   • Columnas clave: 'Ticket ID'
   • Origen: Generado desde análisis de Freshdesk

📌 Archivo adicional requerido:
   • Agentes: Excel con columnas 'ID', 'Agente', 'MAIL'

📌 Flujo:
   1. Seleccionar archivo de tickets (Tipo 1 - Reporte sin actividad)
   2. Seleccionar archivo de agentes
   3. Elegir modo (Manual/Automático)
   4. Sistema procesa y envía notas automáticamente

🔄 SINCRONIZAR ESTADOS (FRESHDESK → CLARITY):

📌 Propósito:
   • Mantener consistencia en estados entre ambos sistemas
   • Aplicar cambios masivos de estados desde Freshdesk a Clarity

📌 Archivo Freshdesk requerido:
   • TIPO: Lista Completa de Tickets (periodo 1 año)
   • Columnas clave: 'Ticket ID' y 'Estado'
   • Origen: Exportación completa de Freshdesk

📌 Archivo Clarity requerido:
   • CSV con formato específico de Clarity (exportación directa)

📌 Flujo:
   1. Cargar archivo Freshdesk (Tipo 2 - Lista completa)
   2. Cargar archivo Clarity (CSV en formato Clarity)
   3. Verificación de estructura
   4. Análisis de diferencias
   5. Confirmación de cambios
   6. Aplicación en Clarity
"""

def get_sync_guide(self):
        return """
╔══════════════════════════════════════════════╗
║           🔄 GUÍA DE SINCRONIZACIÓN         ║
╚══════════════════════════════════════════════╝

🎯 MAPEO DE ESTADOS:

El sistema traduce automáticamente entre los estados de ambos sistemas:

   FRESHDESK → CLARITY
   • Open                    → Abierta
   • Closed                  → Cerrada  
   • Resolved                → Resuelto
   • Waiting on Customer     → Esperando al cliente
   • Forwarded to Manufacturer → Derivado al fabricante
   • In Progress             → En progreso
   • Pending                 → En evaluación

📋 FLUJO DE SINCRONIZACIÓN:

1. PREPARACIÓN:
   • Exportar tickets desde Freshdesk (Excel)
   • Exportar datos desde Clarity (CSV)

2. CARGA:
   • Seleccionar archivo Freshdesk (.xlsx)
   • Seleccionar archivo Clarity (.csv)

3. ANÁLISIS:
   • Sistema verifica estructura de archivos
   • Detecta diferencias en estados
   • Muestra resumen de cambios propuestos

4. CONFIRMACIÓN:
   • Revisar cambios propuestos
   • Opción: Aplicar cambios o descargar Excel para revisión

5. APLICACIÓN:
   • Sistema aplica cambios en Clarity automáticamente
   • Muestra reporte final con éxitos y errores

⚠️  RECOMENDACIONES:
   • Realizar backup de datos antes de sincronizaciones masivas
   • Probar con pocos tickets primero
   • Revisar el reporte de diferencias antes de aplicar
"""

def get_troubleshooting_guide(self):
      return """
   ╔══════════════════════════════════════════════╗
   ║           🔧 SOLUCIÓN DE PROBLEMAS          ║
   ╚══════════════════════════════════════════════╝

   🚨 PROBLEMAS COMUNES Y SOLUCIONES:

   ❌ "Error de autenticación en Freshdesk"
      • Verificar que la API Key sea correcta
      • Confirmar que el dominio esté bien escrito (ej: https://empresa.freshdesk.com)
      • Asegurar que la API Key tenga permisos necesarios

   ❌ "No se puede conectar a Clarity"
      • Verificar usuario y contraseña
      • Confirmar formato del dominio (ej: https://pmservice.empresa.com:puerto/ppm/rest/v1)
      • Verificar que el usuario tenga permisos en Clarity

   ❌ "Error al cargar archivo CSV"
      • Verificar que el archivo tenga formato CSV válido
      • Revisar que tenga las columnas requeridas
      • Asegurar que el archivo no esté corrupto o en uso por otro programa

   ❌ "No se encuentran diferencias entre archivos"
      • Verificar que los Ticket ID coincidan en ambos archivos
      • Confirmar que los archivos correspondan al mismo período
      • Revisar que haya tickets con estados diferentes

   ❌ "Error en envío de notas internas"
      • Verificar formato del archivo de agentes
      • Confirmar que los IDs de agentes existan en Freshdesk
      • Revisar permisos de la API Key para enviar notas

   ❌ "El sistema se cierra inesperadamente"
      • Verificar que tenga .NET Framework actualizado (Windows)
      • Cerrar otros programas que puedan consumir mucha memoria
      • Ejecutar el sistema como administrador si es necesario

   📁 INFORMACIÓN SOBRE REGISTROS (LOGS):

   El sistema genera registros automáticamente para ayudar en la solución de problemas:

      📍 Ubicación: Los logs se guardan en la carpeta 'logs' junto al ejecutable
      📅 Rotación: Los logs se mantienen por 30 días y luego se eliminan automáticamente
      🔒 Privacidad: Los logs contienen información técnica pero NO contraseñas

   📞 SOPORTE TÉCNICO:

   Si los problemas persisten, contacte al soporte técnico:

      📧 Email: matiasruibal372@gmail.com
      📝 Asunto: 🚨 INCIDENTE SISTEMA FRESHDESK - Asistencia Urgente Requerida

   Por favor, incluya en su mensaje:

      1. El mensaje de error COMPLETO que aparece en pantalla
      2. Los pasos exactos que realizó antes del error
      3. La operación específica que estaba intentando realizar
      4. Los archivos de log correspondientes al día del problema (adjuntar)

   ⚠️ RECOMENDACIONES GENERALES:
      • Mantener una copia de los archivos originales antes de cualquier proceso
      • Verificar formatos de archivo según la guía en la sección "Formatos"
      • Realizar pruebas con pocos registros antes de procesamientos masivos
      • Asegurar conexión a internet estable durante operaciones con APIs
   """

def get_section(self, section_key):
        return self.sections.get(section_key, "Sección no encontrada")

def list_sections(self):
        return [
            ("intro", "🚀 Introducción al Sistema"),
            ("config", "🔧 Configuración"), 
            ("reports", "📊 Reportes"),
            ("processes", "⚙️ Procesos"),
            ("formats", "📁 Formatos de Archivos"),
            ("sync", "🔄 Guía de Sincronización"),
            ("troubleshoot", "🔧 Solución de Problemas")
        ]