"""Configuración editable por el profesor.

Cambie los valores de esta sección antes de distribuir el juego.
"""

APP_TITLE = "Misión Digital: Atajos de Oficina"

# Opciones válidas: "primaria", "secundaria" o "preparatoria".
NIVEL_EDUCATIVO = "secundaria"

# IMPORTANTE: cambie esta contraseña antes de usar el programa.
CONTRASENA_PROFESOR = "Profesor2026!"

# True activa pantalla completa, siempre visible y bloqueo de atajos de Windows.
MODO_QUIOSCO_ESTRICTO = True

# Guarda automáticamente nivel y ejercicio actual en el perfil de Windows.
GUARDAR_PROGRESO = True

# Segundos que permanece visible el mensaje de acierto.
DURACION_MENSAJE_MS = 850


# Los grupos son acumulativos: secundaria incluye primaria y preparatoria incluye
# primaria + secundaria. Para agregar ejercicios, copie uno y cambie sus datos.
ATAJOS_POR_NIVEL = {
    "primaria": [
        {"id": "copiar", "texto": "Copia el elemento seleccionado", "atajo": "Ctrl+C"},
        {"id": "pegar", "texto": "Pega el elemento copiado", "atajo": "Ctrl+V"},
        {"id": "deshacer", "texto": "Deshaz la última acción", "atajo": "Ctrl+Z"},
        {"id": "seleccionar_todo", "texto": "Selecciona todo", "atajo": "Ctrl+A"},
        {"id": "guardar", "texto": "Guarda el documento", "atajo": "Ctrl+S"},
        {"id": "imprimir", "texto": "Abre la opción de impresión", "atajo": "Ctrl+P"},
    ],
    "secundaria": [
        {"id": "cortar", "texto": "Corta el elemento seleccionado", "atajo": "Ctrl+X"},
        {"id": "rehacer", "texto": "Rehaz la última acción", "atajo": "Ctrl+Y"},
        {"id": "buscar", "texto": "Busca una palabra", "atajo": "Ctrl+F"},
        {"id": "negrita", "texto": "Activa o desactiva negritas", "atajo": "Ctrl+B"},
        {"id": "cursiva", "texto": "Activa o desactiva cursivas", "atajo": "Ctrl+I"},
        {"id": "subrayado", "texto": "Activa o desactiva subrayado", "atajo": "Ctrl+U"},
    ],
    "preparatoria": [
        {"id": "nuevo", "texto": "Crea un documento nuevo", "atajo": "Ctrl+N"},
        {"id": "abrir", "texto": "Abre un archivo", "atajo": "Ctrl+O"},
        {"id": "guardar_como", "texto": "Abre Guardar como", "atajo": "Ctrl+Shift+S"},
        {"id": "cerrar_pestana", "texto": "Cierra la pestaña actual", "atajo": "Ctrl+W"},
        {"id": "cambiar_pestana", "texto": "Cambia a la siguiente pestaña", "atajo": "Ctrl+Tab"},
        {"id": "reemplazar", "texto": "Abre Buscar y reemplazar", "atajo": "Ctrl+H"},
    ],
}


TAREAS_WORD_POR_NIVEL = {
    "primaria": [
        {"id": "word_negrita", "texto": "Pon el texto en negritas", "accion": "negrita", "atajo": "Ctrl+B", "alternativos": ["Ctrl+N"]},
        {"id": "word_cursiva", "texto": "Pon el texto en cursiva", "accion": "cursiva", "atajo": "Ctrl+I", "alternativos": ["Ctrl+K"]},
        {"id": "word_subrayado", "texto": "Subraya el texto", "accion": "subrayado", "atajo": "Ctrl+U", "alternativos": ["Ctrl+S"]},
        {"id": "word_centrar", "texto": "Centra el párrafo", "accion": "centrar", "atajo": "Ctrl+E", "alternativos": ["Ctrl+T"]},
        {"id": "word_izquierda", "texto": "Alinea el párrafo a la izquierda", "accion": "izquierda", "atajo": "Ctrl+L", "alternativos": ["Ctrl+Q"]},
        {"id": "word_lista", "texto": "Convierte el texto en una lista con viñetas", "accion": "vinetas", "atajo": None},
        {"id": "word_color", "texto": "Cambia el color de la fuente", "accion": "color_fuente", "atajo": None},
        {"id": "word_imprimir", "texto": "Abre la impresión del documento", "accion": "imprimir", "atajo": "Ctrl+P"},
    ],
    "secundaria": [
        {"id": "word_justificar", "texto": "Justifica el párrafo", "accion": "justificar", "atajo": "Ctrl+J"},
        {"id": "word_resaltar", "texto": "Resalta el texto seleccionado", "accion": "resaltar", "atajo": None},
        {"id": "word_tamano", "texto": "Aumenta el tamaño de la fuente", "accion": "aumentar_fuente", "atajo": "Ctrl+Shift+>"},
        {"id": "word_tabla", "texto": "Inserta una tabla en el documento", "accion": "tabla", "atajo": None},
    ],
    "preparatoria": [
        {"id": "word_interlineado", "texto": "Cambia el interlineado del párrafo", "accion": "interlineado", "atajo": None},
        {"id": "word_columnas", "texto": "Organiza el documento en columnas", "accion": "columnas", "atajo": None},
        {"id": "word_encabezado", "texto": "Agrega un encabezado al documento", "accion": "encabezado", "atajo": None},
        {"id": "word_hipervinculo", "texto": "Inserta un hipervínculo", "accion": "hipervinculo", "atajo": "Ctrl+K"},
    ],
}

TAREAS_POWERPOINT_POR_NIVEL = {
    "primaria": [
        {"id": "ppt_nueva", "texto": "Agrega una nueva diapositiva", "accion": "nueva_diapositiva", "atajo": "Ctrl+M"},
        {"id": "ppt_diseno", "texto": "Cambia el diseño de la diapositiva", "accion": "diseno", "atajo": None},
        {"id": "ppt_negrita", "texto": "Pon el título en negritas", "accion": "negrita", "atajo": "Ctrl+B", "alternativos": ["Ctrl+N"]},
        {"id": "ppt_centrar", "texto": "Centra el título", "accion": "centrar", "atajo": "Ctrl+E", "alternativos": ["Ctrl+T"]},
        {"id": "ppt_forma", "texto": "Inserta una forma", "accion": "insertar_forma", "atajo": None},
        {"id": "ppt_presentar", "texto": "Inicia la presentación desde el principio", "accion": "presentar", "atajo": "F5"},
    ],
    "secundaria": [
        {"id": "ppt_imagen", "texto": "Inserta una imagen en la diapositiva", "accion": "imagen", "atajo": None},
        {"id": "ppt_duplicar", "texto": "Duplica la diapositiva actual", "accion": "duplicar", "atajo": "Ctrl+Shift+D"},
        {"id": "ppt_transicion", "texto": "Aplica una transición a la diapositiva", "accion": "transicion", "atajo": None},
        {"id": "ppt_alinear", "texto": "Alinea los objetos al centro", "accion": "alinear_objetos", "atajo": None},
    ],
    "preparatoria": [
        {"id": "ppt_animacion", "texto": "Agrega una animación al objeto", "accion": "animacion", "atajo": None},
        {"id": "ppt_notas", "texto": "Agrega notas del presentador", "accion": "notas", "atajo": None},
        {"id": "ppt_orden", "texto": "Envía el objeto al fondo", "accion": "enviar_fondo", "atajo": None},
        {"id": "ppt_presentar_actual", "texto": "Inicia la presentación desde la diapositiva actual", "accion": "presentar_actual", "atajo": "Shift+F5"},
    ],
}

TAREAS_EXCEL_POR_NIVEL = {
    "primaria": [
        {"id": "excel_negrita", "texto": "Pon la celda activa en negritas", "accion": "negrita", "atajo": "Ctrl+B", "alternativos": ["Ctrl+N"]},
        {"id": "excel_bordes", "texto": "Agrega bordes a la celda", "accion": "bordes", "atajo": None},
        {"id": "excel_moneda", "texto": "Aplica formato de moneda", "accion": "moneda", "atajo": "Ctrl+Shift+4"},
        {"id": "excel_porcentaje", "texto": "Aplica formato de porcentaje", "accion": "porcentaje", "atajo": "Ctrl+Shift+5"},
        {"id": "excel_combinar", "texto": "Combina y centra las celdas", "accion": "combinar", "atajo": None},
        {"id": "excel_autosuma", "texto": "Inserta una Autosuma desde la cinta", "accion": "autosuma", "atajo": None},
        {"id": "excel_ordenar", "texto": "Ordena los datos de A a Z", "accion": "ordenar", "atajo": None},
    ],
    "secundaria": [
        {"id": "excel_filtro", "texto": "Activa un filtro para los datos", "accion": "filtro", "atajo": "Ctrl+Shift+L"},
        {"id": "excel_grafico", "texto": "Inserta un gráfico con los datos", "accion": "grafico", "atajo": None},
        {"id": "excel_promedio", "texto": "Calcula el promedio de los precios", "accion": "promedio", "atajo": None},
        {"id": "excel_fecha", "texto": "Aplica formato de fecha a la celda", "accion": "fecha", "atajo": None},
    ],
    "preparatoria": [
        {"id": "excel_condicional", "texto": "Aplica formato condicional a los datos", "accion": "formato_condicional", "atajo": None},
        {"id": "excel_inmovilizar", "texto": "Inmoviliza la fila superior", "accion": "inmovilizar", "atajo": None},
        {"id": "excel_validacion", "texto": "Agrega validación de datos", "accion": "validacion", "atajo": None},
        {"id": "excel_tabla", "texto": "Convierte el rango en una tabla", "accion": "tabla_excel", "atajo": "Ctrl+T"},
    ],
}

# Alias conservados para extensiones antiguas del proyecto.
TAREAS_WORD = TAREAS_WORD_POR_NIVEL["primaria"]
TAREAS_POWERPOINT = TAREAS_POWERPOINT_POR_NIVEL["primaria"]
TAREAS_EXCEL = TAREAS_EXCEL_POR_NIVEL["primaria"]
