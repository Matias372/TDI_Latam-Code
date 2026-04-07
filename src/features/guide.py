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
║     BIENVENIDO A SYNC DESK MANAGER        ║
╚══════════════════════════════════════════════╝

DESCRIPCIÓN GENERAL:
   SyncDesk Manager - Sistema de Gestión de Tickets
   Herramienta para sincronizar y gestionar tickets entre Freshdesk y Clarity

FUNCIONALIDADES PRINCIPALES:
   • Sincronización de estados entre Freshdesk y Clarity
   • Generación de reportes y análisis
   • Envío automatizado de notas internas
   • Monitoreo de tickets inactivos

ARQUITECTURA:
   • Freshdesk ←→ SyncDesk Manager ←→ Clarity
   • Procesamiento por lotes desde archivos Excel/CSV
   • Interfaz de consola amigable con menús intuitivos
"""

    def get_configuration_guide(self):
        return """
╔══════════════════════════════════════════════╗
║             CONFIGURACIÓN                 ║
╚══════════════════════════════════════════════╝

CONFIGURACIÓN DE FRESHDESK:

API Key de Freshdesk:
   • Obtener desde: https://[tu-dominio].freshdesk.com/admin/apikey
   • La API Key es necesaria para todas las operaciones

Dominio de Freshdesk:
   • Formato: https://[nombre-empresa].freshdesk.com
   • Ejemplo: https://mitienda.freshdesk.com

CONFIGURACIÓN DE CLARITY:

Credenciales de Clarity:
   • Usuario y contraseña proporcionados por el administrador
   • Mismas credenciales que usas para acceder a Clarity vía web

Dominio de Clarity:
   • Formato automático: https://pmservice.[empresa].com:[puerto]/ppm/rest/v1
   • Ejemplo: https://pmservice.ejemplo.com:1234/ppm/rest/v1

CONFIGURACIÓN POR ARCHIVO TXT:

Puedes crear un archivo config.txt con este formato:

   API_Freshdesk: tu_api_key_aqui
   Freshdesk_domain: https://tudominio.freshdesk.com
   Clarity_user: tu_usuario_clarity
   Clarity_pass: tu_contraseña_clarity
   Clarity_domain: https://pmservice.empresa.com:puerto/ppm/rest/v1

NOTAS TÉCNICAS ADICIONALES:

REGENERACIÓN DE ETIQUETAS CLARITY:
   • La API de Freshdesk permite 500 requests por minuto
   • Cada ticket requiere 2 requests (NULL + Restauración)
   • Límite práctico: 250 tickets por ejecución
   • Los procesos masivos deben dividirse en lotes de 250 tickets

FORMATOS DE ARCHIVOS:
   • Siempre verificar las columnas requeridas en cada proceso
   • Los archivos deben provenir de exportaciones oficiales de Freshdesk
   • No modificar la estructura de archivos CSV de Clarity
"""

    def get_reports_guide(self):
      return """
   ╔══════════════════════════════════════════════╗
   ║               REPORTES                    ║
   ╚══════════════════════════════════════════════╝

   TICKETS SIN ETIQUETAS:
      • Propósito: Identificar tickets que no tienen etiquetas asignadas
      • Fuente: Consulta directa a la API de Freshdesk
      • Salida: Excel con tickets sin etiquetas y su información básica

   LISTA DE EMPRESAS:
      • Propósito: Obtener listado completo de empresas en Freshdesk
      • Fuente: API de Freshdesk
      • Salida: Excel con empresas y sus dominios

   PRODUCTOS DIFERENTES (FRESHDESK vs CLARITY):
      • Propósito: Detectar discrepancias en productos asignados
      • Archivos requeridos:
         - Freshdesk: Lista Completa de Tickets (con columna 'Producto')
         - Clarity: CSV con formato específico (exportación directa de Clarity)
      • Salida: Excel en carpeta Descargas con diferencias encontradas
   """

    def get_file_formats_guide(self):
      return """
   ╔══════════════════════════════════════════════╗
   ║             FORMATOS DE ARCHIVOS          ║
   ╚══════════════════════════════════════════════╝

   ARCHIVOS FRESHDESK (EXCEL) - TRES TIPOS:

   TIPO 1: REPORTE DE TICKETS SIN ACTIVIDAD
      • Propósito: Envío de notas internas a tickets inactivos
      • Columnas clave: 'Ticket ID'

   TIPO 2: LISTA COMPLETA DE TICKETS (PERIODO 1 AÑO)
      • Propósito: Sincronización de estados y reporte de productos diferentes
      • Columnas clave: 'Ticket ID', 'Estado', 'Producto'

   TIPO 3: REGENERACIÓN DE ETIQUETAS CLARITY
      • Propósito: Forzar generación de etiquetas CREATE CLARITY
      • Columnas requeridas EXACTAS:
         - Ticket ID → Identificador único (numérico)
         - Segmento → Valor del segmento (no vacío)
         - Fabricante → Valor del fabricante (no vacío)  
         - Producto → Valor del producto (no vacío)

      IMPORTANTE:
         - Los campos Segmento, Fabricante y Producto NO deben estar vacíos
         - El archivo debe provenir de exportación Freshdesk con estos campos
         - Los Ticket ID deben existir en Freshdesk

   ARCHIVO CLARITY (CSV - FORMATO ESPECÍFICO):
      • Exportación DIRECTA de Clarity sin modificar formato
      • Columnas requeridas: 'ID', 'Estado Freshdesk', 'Producto TDI'

   ARCHIVO DE AGENTES (EXCEL):
      • Columnas: 'ID', 'Agente', 'MAIL'
   """

    def get_processes_guide(self):
      return """
   ╔══════════════════════════════════════════════╗
   ║               PROCESOS                     ║
   ╚══════════════════════════════════════════════╝

   REVISAR TICKETS SIN ACTIVIDAD:

   Propósito:
      • Enviar notas internas a tickets inactivos por más de 10 días
      • Recordar a agentes sobre tickets pendientes

   Archivos requeridos:
      • Freshdesk: Reporte de Tickets sin Actividad (con 'Ticket ID')
      • Agentes: Excel con columnas 'ID', 'Agente', 'MAIL'

   Flujo:
      1. Seleccionar archivo de tickets (Tipo 1)
      2. Seleccionar archivo de agentes
      3. Elegir modo (Manual/Automático)
      4. Sistema procesa y envía notas automáticamente

   SINCRONIZAR ESTADOS (FRESHDESK → CLARITY):

   Propósito:
      • Mantener consistencia en estados entre ambos sistemas
      • Aplicar cambios masivos de estados desde Freshdesk a Clarity

   Archivos requeridos:
      • Freshdesk: Lista Completa de Tickets (con 'Ticket ID' y 'Estado')
      • Clarity: CSV con formato específico (exportación directa)

   Flujo:
      1. Cargar archivo Freshdesk (Tipo 2)
      2. Cargar archivo Clarity (CSV formato Clarity)
      3. Verificación de estructura
      4. Análisis de diferencias
      5. Confirmación de cambios
      6. Aplicación en Clarity

   FORZAR REGENERACIÓN DE ETIQUETAS CREATE CLARITY:

   Propósito:
      • Actualizar tickets para que el sistema detecte cambios y ejecute escenarios de etiquetas
      • Generar etiquetas CREATE CLARITY que permitan crear tickets secundarios en Clarity
      • Solucionar casos donde no se generó el ticket en la ticketera Clarity

   Archivo Excel requerido:
      • TIPO: Regeneración de Etiquetas Clarity
      • Columnas requeridas: 'Ticket ID', 'Segmento', 'Fabricante', 'Producto'
      • Origen: Exportación de Freshdesk con campos necesarios

   Condiciones para procesar tickets:
      • Sin etiquetas CREATE CLARITY o UPDATE CLARITY existentes
      • Con grupo asignado (excluye: TRIAGE CHILE, SOPORTE N0)
      • Con agente asignado
      • Con tipo asignado (verificado internamente)
      • Campos Segmento, Fabricante y Producto completos en Excel

   Flujo automático:
      1. Seleccionar archivo Excel con tickets
      2. Validación automática de condiciones por ticket
      3. Proceso en 2 pasos: NULL → Restauración de campos
      4. Freshdesk detecta cambios y genera etiquetas automáticamente
      5. Sistema envía email a Clarity para crear ticket secundario

   Consideraciones técnicas:
      • Límite API: 500 requests/minuto → Máximo 250 tickets por ejecución (2 requests/ticket)
      • Tickets fallidos: Se reportan al final para revisión manual
      • Proceso: Completamente automático, sin confirmación por ticket
   """

    def get_sync_guide(self):
         return """
   ╔══════════════════════════════════════════════╗
   ║           GUÍA DE SINCRONIZACIÓN          ║
   ╚══════════════════════════════════════════════╝

   MAPEO DE ESTADOS:

   El sistema traduce automáticamente entre los estados de ambos sistemas:

      FRESHDESK → CLARITY
      • Open                    → Abierta
      • Closed                  → Cerrada  
      • Resolved                → Resuelto
      • Waiting on Customer     → Esperando al cliente
      • Forwarded to Manufacturer → Derivado al fabricante
      • In Progress             → En progreso
      • Pending                 → En evaluación

   FLUJO DE SINCRONIZACIÓN:

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

   RECOMENDACIONES:
      • Realizar backup de datos antes de sincronizaciones masivas
      • Probar con pocos tickets primero
      • Revisar el reporte de diferencias antes de aplicar
   """

    def get_troubleshooting_guide(self):
         return """
      ╔══════════════════════════════════════════════╗
      ║           SOLUCIÓN DE PROBLEMAS           ║
      ╚══════════════════════════════════════════════╝

      PROBLEMAS COMUNES Y SOLUCIONES:

       "Error de autenticación en Freshdesk"
         • Verificar que la API Key sea correcta
         • Confirmar que el dominio esté bien escrito (ej: https://empresa.freshdesk.com)
         • Asegurar que la API Key tenga permisos necesarios

       "No se puede conectar a Clarity"
         • Verificar usuario y contraseña
         • Confirmar formato del dominio (ej: https://pmservice.empresa.com:puerto/ppm/rest/v1)
         • Verificar que el usuario tenga permisos en Clarity

       "Error al cargar archivo CSV"
         • Verificar que el archivo tenga formato CSV válido
         • Revisar que tenga las columnas requeridas
         • Asegurar que el archivo no esté corrupto o en uso por otro programa

       "No se encuentran diferencias entre archivos"
         • Verificar que los Ticket ID coincidan en ambos archivos
         • Confirmar que los archivos correspondan al mismo período
         • Revisar que haya tickets con estados diferentes

       "Error en envío de notas internas"
         • Verificar formato del archivo de agentes
         • Confirmar que los IDs de agentes existan en Freshdesk
         • Revisar permisos de la API Key para enviar notas

       "El sistema se cierra inesperadamente"
         • Verificar que tenga .NET Framework actualizado (Windows)
         • Cerrar otros programas que puedan consumir mucha memoria
         • Ejecutar el sistema como administrador si es necesario
      
       "Error en regeneración de etiquetas CLARITY"
         • Verificar que el archivo tenga columnas EXACTAS: Ticket ID, Segmento, Fabricante, Producto
         • Confirmar que los campos Segmento, Fabricante y Producto no estén vacíos
         • Revisar que los Ticket ID existan en Freshdesk
         • Verificar límite de API (máximo 250 tickets por ejecución)
         • Tickets fallidos se reportan al final del proceso

       "El proceso de regeneración se detiene"
         • Posible límite de API alcanzado - esperar 1 minuto y reintentar con menos tickets
         • Verificar conexión a internet estable

       INFORMACIÓN SOBRE REGISTROS (LOGS):

      El sistema genera registros automáticamente para ayudar en la solución de problemas:

          Ubicación: Los logs se guardan en la carpeta 'logs' junto al ejecutable
          Rotación: Los logs se mantienen por 30 días y luego se eliminan automáticamente
          Privacidad: Los logs contienen información técnica pero NO contraseñas

       SOPORTE TÉCNICO:

      Si los problemas persisten, contacte al soporte técnico:

          Email: matiasruibal372@gmail.com
          Asunto:  INCIDENTE SyncDesk Manager - Asistencia Urgente Requerida

      Por favor, incluya en su mensaje:

         1. El mensaje de error COMPLETO que aparece en pantalla
         2. Los pasos exactos que realizó antes del error
         3. La operación específica que estaba intentando realizar
         4. Los archivos de log correspondientes al día del problema (adjuntar)

       RECOMENDACIONES GENERALES:
         • Mantener una copia de los archivos originales antes de cualquier proceso
         • Verificar formatos de archivo según la guía en la sección "Formatos"
         • Realizar pruebas con pocos registros antes de procesamientos masivos
         • Asegurar conexión a internet estable durante operaciones con APIs
      """

    def get_section(self, section_key):
         return self.sections.get(section_key, "Sección no encontrada")

    def list_sections(self):
         return [
               ("intro", " Introducción al Sistema"),
               ("config", " Configuración"), 
               ("reports", " Reportes"),
               ("processes", " Procesos"),
               ("formats", " Formatos de Archivos"),
               ("sync", " Guía de Sincronización"),
               ("troubleshoot", " Solución de Problemas")
         ]