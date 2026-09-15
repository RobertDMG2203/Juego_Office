# Misión Digital

**Misión Digital** es un juego educativo de escritorio para **Windows 10/11** diseñado para enseñar atajos de teclado y herramientas básicas de ofimática mediante una experiencia guiada, visual y controlada. El proyecto está pensado para instalarse en computadoras escolares durante un ciclo escolar completo y permitir que cada estudiante avance con su propia matrícula, mientras el profesor consulta resultados desde un panel protegido por contraseña.

El juego **no controla Microsoft Office real**. Word, PowerPoint y Excel están simulados dentro de la aplicación para que el estudiante pueda practicar sin modificar archivos ni depender de una instalación de Office.

---

## Objetivo pedagógico

El estudiante practica cuatro áreas:

1. **Teclado y atajos**: combinaciones como copiar, pegar, guardar, buscar, formato y otros atajos acumulativos según el nivel educativo.
2. **Word simulado**: formato, alineación, viñetas, tablas y herramientas avanzadas según el nivel.
3. **PowerPoint simulado**: diapositivas, diseño, formas, imágenes, transiciones, animaciones y presentación.
4. **Excel simulado**: formato de celdas, autosuma desde la cinta, filtros, gráficos, fórmulas y herramientas de datos.

El profesor puede configurar la dificultad entre:

- **Primaria**
- **Secundaria**
- **Prepa / preparatoria**

Los ejercicios son acumulativos: secundaria incluye el contenido de primaria y preparatoria incluye los grupos anteriores. En Secundaria y Prepa también se habilitan más herramientas dentro de Word, PowerPoint y Excel.

---

# Experiencia del estudiante

<img width="2559" height="1565" alt="Captura de pantalla 2026-09-14 175530" src="https://github.com/user-attachments/assets/11e67f3f-d373-4ccd-8732-81cffe945522" />
<img width="1792" height="1088" alt="Captura de pantalla 2026-09-14 175605" src="https://github.com/user-attachments/assets/a6441eba-0791-4fcd-aef5-e80a74d571b4" />

Al iniciar, el estudiante debe registrar:

- nombre completo;
- matrícula;
- grupo.

La **matrícula funciona como identificador del progreso local**. El estudiante puede cambiar libremente entre los cuatro niveles desde la barra superior y el avance de cada nivel se conserva por separado.

La aplicación registra intentos correctos e incorrectos, tareas completadas, precisión y calificación. Al completar los cuatro niveles puede finalizar la sesión; la salida normal solicita contraseña del profesor. También existe una **Salida profesor** anticipada protegida por contraseña.

La interfaz utiliza un tema oscuro moderno, componentes redondeados y un teclado visual negro estilo con profundidad 3D y retroiluminación. Las **hojas de trabajo simuladas** de Word, PowerPoint y Excel se mantienen blancas para parecerse al entorno real de oficina. Cuando el estudiante presiona una tecla física, su equivalente en pantalla se ilumina para reforzar la asociación visual.

El profesor puede decidir desde Configuración si la pista de la esquina superior derecha (atajo esperado o indicación de usar la cinta) se muestra o se oculta durante las misiones.

---

# Panel del profesor

Desde la pantalla inicial existe el botón **Panel del profesor**. El acceso requiere la contraseña docente vigente.

El panel se divide en cuatro apartados.

## Dashboard

<img width="1792" height="1088" alt="Captura de pantalla 2026-09-14 175605" src="https://github.com/user-attachments/assets/5648b559-f6fb-4de7-8b41-e40ef7f50a30" />

<img width="1749" height="1213" alt="Captura de pantalla 2026-09-14 175624" src="https://github.com/user-attachments/assets/16971bfd-c409-4f37-a4b7-728456246e5c" />

Lee automáticamente el histórico de sesiones guardado en `resumen_sesiones.csv` y presenta:

- total de sesiones;
- estudiantes únicos;
- promedio general de calificación;
- precisión promedio;
- tendencia de las últimas 15 sesiones;
- promedio por grupo;
- tabla de las sesiones recientes;
- filtro **Todos los estudiantes** o por matrícula individual;
- detalle de un alumno con doble clic, incluyendo historial y desempeño por nivel cuando existen logs detallados;
- interpretación automática del desempeño general y de los grupos.

El archivo CSV puede abrirse directamente con Excel.

## Importar / Exportar

<img width="1784" height="1200" alt="Captura de pantalla 2026-09-14 175641" src="https://github.com/user-attachments/assets/c9a71362-0de3-4b1a-a9e6-fdffb26e3ec2" />

Permite consolidar resultados cuando el juego está instalado de forma independiente en cada computadora.

- **Exportar al Escritorio:** crea `Escritorio\Mision_Digital_Resultados` y genera un paquete por matrícula con `resultados.csv`, `manifest.json` y los logs detallados disponibles.
- **Importar:** el profesor puede seleccionar una carpeta que contenga uno o muchos paquetes. Las sesiones se deduplican automáticamente, por lo que volver a importar el mismo paquete no duplica datos.
- El dashboard combina resultados locales e importados y permite verlos todos juntos o filtrar un alumno.
- Los datos importados se almacenan en `%LOCALAPPDATA%\MisionDigital\importados`.

Flujo sugerido al terminar una etapa o ciclo:

1. En cada equipo del alumno, entrar al Panel del profesor y pulsar **Exportar al Escritorio**.
2. Copiar las carpetas `Mision_Digital_Resultados` a una USB, recurso de red o almacenamiento institucional.
3. En la computadora del profesor, reunir las carpetas de todos los alumnos dentro de una carpeta común.
4. Abrir **Importar / Exportar** y seleccionar esa carpeta común.
5. Usar el Dashboard en vista **Todos los estudiantes** o seleccionar una matrícula para verla individualmente.

## Configuración

<img width="1789" height="1206" alt="Captura de pantalla 2026-09-14 175658" src="https://github.com/user-attachments/assets/eea1434a-0dc5-4e50-bff6-6da514d4fcec" />

Permite:

- cambiar el nivel educativo entre Primaria, Secundaria y Prepa;
- mostrar u ocultar las pistas de las misiones;
- cambiar la contraseña del profesor.

La contraseña personalizada **no se almacena en texto plano**. Se guarda mediante **PBKDF2-SHA256 con sal** en el perfil local del equipo.

## Mantenimiento

<img width="1784" height="1206" alt="Captura de pantalla 2026-09-14 175711" src="https://github.com/user-attachments/assets/cca524bf-457f-467d-87b2-68eca4941a0b" />

Pensado especialmente para el final del ciclo escolar.

### Limpiar caché

Elimina únicamente:

- caché propia de la aplicación;
- archivos temporales `.tmp`;
- carpetas `__pycache__` del proyecto cuando se ejecuta desde código.

**No elimina** resultados, progresos ni configuración docente.

### Eliminar registros anteriores

Permite eliminar resultados y logs detallados:

- anteriores a 30 días;
- anteriores a 90 días;
- anteriores a 180 días;
- anteriores a 1 año;
- todos los resultados.

Esta operación conserva el progreso de cada matrícula.

### Borrar datos del ciclo

Elimina:

- resultados del dashboard;
- logs detallados;
- progresos de todas las matrículas;
- caché.

Conserva:

- contraseña del profesor;
- nivel educativo configurado;
- preferencia de mostrar/ocultar pistas.

También se eliminan los resultados importados del ciclo anterior para dejar limpio el dashboard consolidado.

La operación requiere una confirmación reforzada escribiendo `BORRAR CICLO`.

### Desinstalar aplicación

La desinstalación requiere escribir `DESINSTALAR` para evitar activaciones accidentales.

En una versión compilada con PyInstaller, el sistema programa un pequeño script temporal de Windows que espera a que termine el **PID exacto** de la aplicación. Después intenta borrar el ejecutable hasta 60 veces, una vez por segundo, para soportar bloqueos breves de Windows Defender, OneDrive o del propio cierre de Qt. El procedimiento elimina **únicamente archivos propios de Misión Digital**:

- el `MisionDigital.exe` exacto que se está ejecutando;
- `%LOCALAPPDATA%\MisionDigital`;
- la copia opcional del código fuente almacenada por `guardar_codigo_oculto.bat`.

El helper deja un diagnóstico en `%TEMP%\MisionDigital_desinstalacion.log`. Si por una política de Windows el EXE no pudiera borrarse, ese archivo indica el fallo sin tocar ninguna dependencia del sistema.

La desinstalación **no ejecuta `pip uninstall`**, no modifica Python global, no toca `site-packages` y no elimina entornos virtuales de otros proyectos.

Cuando la aplicación se ejecuta directamente desde Python (modo desarrollo), el repositorio y `.mision_digital_venv` se conservan deliberadamente. Esto evita que una prueba de la función **Desinstalar** pueda borrar el código o las herramientas de desarrollo del equipo.

> En las computadoras de estudiantes se recomienda distribuir únicamente `MisionDigital.exe`; de ese modo no existe ningún entorno Python que la aplicación necesite desinstalar.

---

# Dónde se guardan los datos

Misión Digital utiliza el perfil local de Windows:

```text
%LOCALAPPDATA%\MisionDigital\
│
├── configuracion_profesor.json
├── progreso\
│   └── <matricula>.json
├── logs\
│   ├── resumen_sesiones.csv
│   └── <matricula>_AAAAMMDD_HHMMSS.jsonl
├── importados\
│   ├── resumen_importado.csv
│   └── detalle\                  # logs importados deduplicados
├── cache\
└── codigo_fuente\               # opcional, si se usa guardar_codigo_oculto.bat
```

### `configuracion_profesor.json`

Guarda:

- nivel educativo actual;
- preferencia de mostrar/ocultar pistas;
- hash y sal de la contraseña personalizada del profesor.

### `progreso/<matricula>.json`

Guarda:

- avance independiente de cada uno de los cuatro niveles;
- último nivel visitado;
- estado de finalización.

### `logs/*.jsonl`

Contiene eventos detallados de una sesión:

- inicio con fecha y hora;
- logros obtenidos y método utilizado (`cinta:` o `teclado:`);
- niveles terminados;
- estado final **lograda / no lograda** de cada misión;
- cierre de sesión.

Los clics exploratorios sobre la cinta y los comandos equivocados **no se guardan como errores** y no reducen la evaluación. El objetivo es registrar si el alumno consiguió la actividad, no penalizar la exploración.

### `logs/resumen_sesiones.csv`

Una fila por sesión finalizada con campos como:

```text
nombre
matricula
grupo
nivel_educativo
inicio
fin
motivo_salida
logros
no_logradas
tareas_totales
calificacion
completado
```

Por compatibilidad con paquetes generados por versiones anteriores pueden seguir apareciendo las columnas `intentos`, `aciertos`, `errores` o `precision`. En sesiones nuevas, `intentos/aciertos` equivalen únicamente a misiones logradas, `errores` permanece en cero y la interfaz ya no utiliza **Precisión** como criterio.

La **calificación** y **completado** representan el porcentaje de misiones logradas sobre el total configurado para esa sesión. La marca de tiempo permite distinguir varias sesiones del mismo estudiante.

## Cintas de Office y formas de resolver

Word, PowerPoint y Excel utilizan una cinta emulada organizada por pestañas y grupos semejantes a la lógica de Office (Fuente, Párrafo, Diapositivas, Número, Datos, Gráficos, etc.). No utiliza recursos propietarios de Microsoft: los iconos son símbolos y texto propios de la simulación.

Cuando una misión dispone de herramienta y atajo, **ambos métodos son válidos**. La pista muestra por ejemplo `Usa la cinta · o Ctrl+B / Ctrl+N`. Si sólo existe una herramienta de cinta, muestra `Usa la cinta`; si sólo existe un comando, muestra el comando.

## Comparación del grupo en el dashboard

Además del promedio general y la vista individual, el panel docente dibuja líneas de evolución para comparar simultáneamente a todos los alumnos importados. Cada línea corresponde a un estudiante y cada punto a una sesión ordenada por fecha. Para conservar legibilidad se muestran hasta cinco estudiantes por gráfica y se generan automáticamente tantas gráficas como sean necesarias.

---

# Arquitectura técnica

El proyecto está desarrollado en **Python + PySide6 / Qt 6**.

## Archivos principales

```text
MisionDigital/
│
├── main.py                  # flujo principal, inicio, login de estudiante y ventana de juego
├── config.py                # contenido pedagógico y valores iniciales
├── widgets.py               # teclado, cintas y simulaciones Word/PPT/Excel
├── styles.py                # tema visual Qt/QSS
├── game_engine.py           # motor de tareas y validación de atajos
├── kiosk.py                 # bloqueo de atajos de Windows
├── progress_store.py        # persistencia de avance por matrícula
├── session_log.py           # logs JSONL + resumen CSV
├── settings_store.py        # nivel educativo y autenticación docente
├── teacher_dashboard.py     # dashboard, configuración y mantenimiento
├── maintenance.py           # limpieza, retención de registros y desinstalación
├── data_exchange.py         # exportación/importación y consolidación por alumno
│
├── tests/
│   ├── test_engine.py
│   ├── test_settings_store.py
│   └── test_maintenance.py
│
├── requirements.txt
├── iniciar_juego.bat
├── crear_exe.bat
├── crear_exe_diagnostico.bat
├── build_exe.py
├── guardar_codigo_oculto.bat
├── .mision_digital_app
└── README.md
```

## Flujo general

```text
StartWindow
   │
   ├── Panel del profesor
   │      └── TeacherDashboard
   │             ├── Dashboard local + importados
   │             ├── Importación / exportación
   │             ├── TeacherSettings
   │             └── Maintenance
   │
   └── Sesión estudiante
          ├── StudentDialog
          └── GameWindow
                 ├── TaskSequence x 4
                 ├── ProgressStore
                 ├── SessionLogger
                 ├── WindowsShortcutBlocker
                 └── Widgets simulados
```

## Motor de tareas

`game_engine.py` contiene `TaskSequence`, que compara acciones o atajos recibidos con la misión actual. Las tareas de Word, PowerPoint y Excel se declaran en `config.py`, lo cual permite ampliar el contenido sin modificar el motor principal.

Ejemplo conceptual:

```python
{
    "id": "word_negrita",
    "texto": "Pon el texto en negritas",
    "accion": "negrita",
    "atajo": "Ctrl+B"
}
```

Para añadir ejercicios nuevos conviene mantener IDs únicos y, cuando exista una acción visual, implementar su comportamiento en el widget correspondiente.

---

# Modo quiosco y límites de Windows

Cuando `MODO_QUIOSCO_ESTRICTO = True`, la aplicación instala un hook de teclado de bajo nivel que intenta mantener al estudiante dentro de la actividad.

Bloquea o intercepta, entre otros:

- tecla Windows;
- `Alt+Tab`;
- `Alt+Esc`;
- `Ctrl+Esc`;
- `Win+Tab`;
- `Win+Ctrl+D`;
- `Win+Ctrl+←`;
- `Win+Ctrl+→`.

Esto reduce el cambio o creación de escritorios virtuales y la navegación fuera de la aplicación.

## Límite importante

Un programa normal de usuario **no puede bloquear `Ctrl+Alt+Supr`**, ya que Windows procesa esa combinación en el escritorio seguro. Tampoco puede impedir acciones de una cuenta con privilegios administrativos, herramientas de administración remota o todas las funciones posibles de accesibilidad.

Por lo tanto, el hook de Misión Digital es una **medida de control de aula**, no una frontera de seguridad.

Para equipos administrados se recomienda combinarlo con:

- cuenta estándar sin privilegios de administrador;
- políticas de Windows;
- Acceso asignado / configuración de quiosco cuando sea compatible con el entorno escolar.

Mantén siempre una cuenta administrativa de recuperación.

---

# Instalación para desarrollo

## Requisitos

- Windows 10 u 11.
- Python 3.11 o superior recomendado.
- PySide6 6.7 o superior y menor que 7.

Instalación manual aislada:

```powershell
py -3 -m venv .mision_digital_venv
.mision_digital_venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py --windowed
```

El nombre `.mision_digital_venv` es intencional: identifica el entorno como exclusivo de este proyecto. No uses `--system-site-packages`. Las librerías instaladas aquí no alteran las versiones globales ni las de otros entornos virtuales.

`--windowed` evita el modo de pantalla completa y facilita el desarrollo.

También puede ejecutarse:

```text
iniciar_juego.bat
```

---

# Generar el `.exe` para los estudiantes

El método recomendado es distribuir **solamente el EXE**. PyInstaller genera un archivo autocontenido; el estudiante no necesita tener Python ni la carpeta de código.

## Paso 1. Preparar el proyecto

En la computadora del profesor/desarrollador:

1. descarga o clona este repositorio;
2. revisa `config.py`;
3. cambia la contraseña inicial antes de distribuir una imagen nueva si es necesario;
4. prueba `iniciar_juego.bat`.

No publiques en GitHub una contraseña real utilizada actualmente en un grupo escolar.

## Paso 2. Crear el ejecutable

Haz doble clic en:

```text
crear_exe.bat
```

El script:

1. detecta automáticamente `py -3` o `python` y comprueba que sea Python 3.10 o superior;
2. crea `.mision_digital_venv` si todavía no existe;
3. verifica que el Python usado realmente pertenezca a ese venv y aborta si no es así;
4. instala o actualiza las dependencias y PyInstaller **sólo dentro de ese entorno**;
5. ejecuta PyInstaller mediante el Python del venv en modo `--onefile --windowed`;
6. coloca el archivo final **directamente en el Escritorio de Windows**;
7. mantiene la consola abierta al terminar, incluso si ocurre un error.

Durante todo el proceso se crea `compilacion_exe.log` junto al proyecto. Si el EXE no se genera, ese archivo conserva la salida completa de `pip` y PyInstaller para poder identificar la causa.

### Seguridad de dependencias en una computadora de desarrollo

`crear_exe.bat` y `iniciar_juego.bat` usan exclusivamente:

```text
<carpeta del proyecto>\.mision_digital_venv\
```

El Python instalado en Windows se utiliza únicamente para crear ese entorno. Después, todos los comandos `pip` se ejecutan como `...\.mision_digital_venv\Scripts\python.exe -m pip ...`. Por diseño:

- no se actualiza ni degrada una librería global;
- no se modifica el venv de otro proyecto;
- no se ejecuta `pip uninstall` durante la desinstalación;
- borrar el EXE no desinstala PySide6/PyInstaller del sistema porque están encapsulados en el EXE o en el venv local de compilación;
- en modo desarrollo la función **Desinstalar** preserva el repositorio y el venv local.

Si una versión anterior del proyecto dejó una carpeta `.venv`, esta versión **no la reutiliza ni la elimina automáticamente**. Revísala manualmente antes de decidir borrarla, especialmente en una computadora de desarrollo.

Si por alguna razón Windows cerrara la consola normal, ejecuta `crear_exe_diagnostico.bat`: este modo abre una consola persistente y muestra el código de salida del generador.

Resultado esperado:

```text
Escritorio\MisionDigital.exe
```

El script utiliza la ruta real del Escritorio obtenida desde Windows, por lo que también funciona cuando el Escritorio está redirigido por el sistema.

## Paso 3. Copiar a las computadoras de los estudiantes

La opción más limpia es:

1. copiar `MisionDigital.exe` en una memoria USB, carpeta de red o sistema de administración de equipos;
2. copiar **únicamente `MisionDigital.exe`** al Escritorio de cada estudiante;
3. abrirlo una vez para verificar que inicia correctamente;
4. entrar al Panel del profesor y definir el nivel educativo.

No es necesario copiar `.py`, `.mision_digital_venv`, `.venv`, tests ni otras carpetas.

## Copia opcional del código oculta

Si por política de la escuela deseas conservar una copia local del código fuente en la computadora, ejecuta:

```text
guardar_codigo_oculto.bat
```

El script copia el proyecto —excluyendo `.mision_digital_venv`, `.venv`, compilaciones y cachés— en:

```text
%LOCALAPPDATA%\MisionDigital\codigo_fuente
```

y marca la carpeta con atributos **Hidden + System**.

Esto evita que aparezca normalmente en el Explorador, pero **no cifra el código ni evita que un usuario con permisos suficientes active “Mostrar archivos ocultos”**.

Para estudiantes, la mejor opción sigue siendo no copiar el código y entregar solamente el EXE.

---

# Fin del ciclo escolar recomendado

En cada computadora:

1. abre `MisionDigital.exe`;
2. entra a **Panel del profesor**;
3. abre **Importar / Exportar** y usa **Exportar al Escritorio** si quieres conservar los resultados del alumno;
4. copia la carpeta `Mision_Digital_Resultados` a la ubicación institucional elegida;
5. abre **Mantenimiento**;
6. al terminar definitivamente el ciclo, usa **Borrar datos del ciclo**;
7. verifica que el dashboard quede vacío;
8. usa **Desinstalar aplicación**;
9. escribe `DESINSTALAR` cuando se solicite.

La aplicación se cerrará y el proceso de limpieza terminará después del cierre.

Si existe información que deba conservarse institucionalmente, usa preferentemente la exportación del panel antes de borrar o desinstalar.

---

# Pruebas

Las pruebas no visuales se encuentran en `tests/`.

Ejecutar:

```powershell
py -3 -m pip install pytest
py -3 -m pytest -q
```

Cubren:

- normalización y validación de atajos;
- avance de tareas;
- niveles educativos acumulativos;
- configuración docente;
- cambio de contraseña;
- limpieza de caché;
- borrado de históricos por antigüedad;
- reinicio de datos de ciclo;
- preferencia de mostrar/ocultar pistas;
- expansión de herramientas por nivel educativo;
- exportación/importación y deduplicación de resultados.

Las pruebas visuales de Qt deben realizarse en Windows ejecutando `main.py --windowed` o el EXE generado.

---

# Consideraciones de seguridad y privacidad

- Los datos del alumnado se guardan **localmente en cada equipo**.
- El proyecto no envía resultados a Internet.
- Nombre, matrícula y grupo son datos identificables: la escuela debe tratarlos de acuerdo con sus propias reglas de privacidad y conservación.
- La función de borrar ciclo permite retirar esos datos al finalizar el periodo escolar.
- La contraseña del profesor cambiada desde la interfaz se guarda con hash y sal, no como texto plano.
- El valor de contraseña inicial en `config.py` sí forma parte del código fuente; cámbialo antes de publicar/distribuir si no deseas exponer el valor inicial.

---

# Guía para continuar el desarrollo

Antes de modificar el proyecto, conserva estas decisiones de arquitectura salvo que exista una razón concreta para cambiarlas:

1. La aplicación es **local y offline**.
2. Las cuatro aplicaciones son **simulaciones**, no automatización de Office real.
3. El avance se identifica por **matrícula**.
4. Los niveles pueden visitarse libremente sin perder progreso.
5. Los resultados se registran en JSONL y CSV.
6. El acceso docente requiere contraseña.
7. La contraseña personalizada se guarda con PBKDF2, no en texto plano.
8. El panel del profesor concentra configuración, análisis y mantenimiento.
9. El mantenimiento nunca debe borrar archivos fuera de las rutas propias de Misión Digital sin una comprobación explícita.
10. Las operaciones destructivas deben requerir confirmación reforzada.
11. El modo quiosco no debe presentarse como seguridad absoluta de Windows.
12. La distribución recomendada al estudiante es un único `MisionDigital.exe`.

## Prompt base para futuras iteraciones

Puedes utilizar este contexto al iniciar otra sesión de desarrollo:

```text
Estoy desarrollando “Misión Digital”, un juego educativo offline para Windows 10/11 hecho en Python con PySide6/Qt6.

Tiene cuatro niveles navegables libremente: teclado/atajos, Word simulado, PowerPoint simulado y Excel simulado. El progreso se guarda por matrícula y por nivel en %LOCALAPPDATA%\\MisionDigital\\progreso. Cada sesión registra nombre, matrícula, grupo, fecha/hora, misiones logradas/no logradas y calificación. Los clics exploratorios y comandos equivocados no se penalizan ni se guardan como errores. Se generan logs JSONL y un resumen_sesiones.csv.

La pantalla inicial permite iniciar al estudiante o entrar al Panel del profesor con contraseña. El panel contiene un dashboard que combina resultados locales e importados, permite filtrar Todos o una matrícula, abrir el detalle individual con doble clic, comparar simultáneamente a los alumnos mediante gráficas de líneas divididas en grupos visuales de hasta cinco estudiantes, importar/exportar paquetes de resultados, configurar nivel educativo primaria/secundaria/prepa, mostrar u ocultar pistas, cambiar la contraseña mediante PBKDF2 y realizar mantenimiento de fin de ciclo.

Las tareas de Word, PowerPoint y Excel son acumulativas por nivel: Secundaria y Prepa habilitan herramientas adicionales. Las cintas emuladas deben conservar pestañas y grupos visuales semejantes a la lógica de Office. Cuando una misión disponga de cinta y atajo, ambos deben resolverla y la pista debe mostrar ambas opciones. Excel no debe exigir Alt+= en teclado español latino; Autosuma se resuelve desde la cinta. Las hojas simuladas de Word, PowerPoint y Excel deben permanecer blancas, mientras el resto de la interfaz se mantiene moderna, oscura, redondeada y con acentos cyan. El teclado debe verse negro, gamer, 3D y retroiluminado, y animar las teclas al recibir pulsaciones físicas.

Existe un modo quiosco con hook de teclado para bloquear Alt+Tab, tecla Windows y atajos de escritorios virtuales, sabiendo que no puede bloquear Ctrl+Alt+Supr ni sustituye las políticas oficiales de quiosco de Windows.

La distribución recomendada es un único MisionDigital.exe generado con PyInstaller y colocado en el Escritorio. Mantén el aislamiento de dependencias mediante `.mision_digital_venv` y no ejecutes instalaciones/desinstalaciones sobre Python global. No cambies esta arquitectura ni elimines funcionalidades existentes salvo que te lo solicite explícitamente. Al modificar código, mantén compatibilidad con los logs y progresos actuales y actualiza README/tests cuando corresponda.
```

---

# Estado del proyecto

Versión orientada a uso escolar prolongado con:

- cuatro niveles educativos interactivos;
- navegación libre;
- persistencia por matrícula;
- dashboard docente local + consolidado;
- importación/exportación por alumno con deduplicación;
- detalle individual por matrícula;
- configuración de nivel y pistas;
- más herramientas en Secundaria y Prepa;
- hojas de trabajo blancas con entorno oscuro;
- cambio de contraseña;
- registro logrado/no logrado sin penalizar exploración;
- comparativas simultáneas por alumno con fecha y hora por sesión;
- logs y calificación;
- mantenimiento de fin de ciclo;
- desinstalación controlada;
- tema oscuro moderno;
- teclado 3D retroiluminado;
- generación de EXE para Escritorio.

