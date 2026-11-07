"""Capítulo 4, sección 4.1: Desarrollo."""
from docx import Document
from docx.shared import Emu

import cap4_comun as C
import formato as F

P = C.PULGADA


def main():
    doc = Document(str(C.ARCHIVO))
    ancho, alto = C.medidas(doc)
    a = C.antes_de_referencias(doc)

    def tabla(filas, numero, titulo_pie, anclaje, anchos=None, etiqueta=0):
        t = F.tabla(doc, filas, anclaje, anchos=anchos, col_etiqueta=etiqueta)
        return F.pie(doc, f'Tabla {numero}', titulo_pie, t)

    a = F.titulo(doc, 'Capítulo 4. Marco Metodológico: Desarrollo e Implementación',
                 1, a)
    a = F.parrafo(
        doc,
        'Los capítulos precedentes establecieron qué debía construirse y con qué '
        'estructura. El presente capítulo documenta la construcción. La primera '
        'sección describe la plataforma de desarrollo, las tecnologías y '
        'arquitecturas empleadas —con la justificación de cada biblioteca '
        'incorporada— y los mecanismos de seguridad implementados. La segunda '
        'presenta el código fuente del sistema: el inicio de sesión, el menú '
        'principal, las funciones principales de cada módulo y un ejemplo de la '
        'generación de gráficas y reportes. La tercera documenta las pruebas de '
        'implementación realizadas sobre el sistema en funcionamiento.', a)

    a = F.titulo(doc, '4.1 Desarrollo', 2, a)
    a = F.titulo(doc, '4.1.1 Plataforma de desarrollo', 3, a)
    a = F.parrafo(
        doc,
        'El sistema se desarrolló en un equipo personal con sistema operativo '
        'Windows 11, utilizando Visual Studio Code como entorno de edición y Git '
        'como sistema de control de versiones, con el repositorio alojado en '
        'GitHub. Las dependencias de Python se instalaron en un entorno virtual '
        'propio del proyecto, de modo que las versiones empleadas quedaran '
        'aisladas de las del sistema operativo y pudieran reproducirse en el '
        'servidor a partir del archivo de requerimientos.', a)
    a = F.parrafo(
        doc,
        'El entorno de desarrollo y el de producción se distinguen en un solo '
        'punto: el motor de base de datos. En desarrollo se utiliza SQLite, que '
        'no requiere servidor y permite reconstruir la base completa borrando un '
        'archivo; en producción se utiliza PostgreSQL. El resto del código es '
        'idéntico, porque el acceso a los datos se realiza siempre a través del '
        'mapeador objeto-relacional del framework y no mediante sentencias '
        'escritas para un motor concreto. La selección del motor se resuelve por '
        'variable de entorno, de manera que el mismo código fuente opera en ambos '
        'entornos sin modificación.', a)
    a = F.parrafo(
        doc,
        'El despliegue se realiza sobre una instancia EC2 de Amazon Web Services '
        'del tipo t3.small, con dos núcleos virtuales y dos gigabytes de memoria, '
        'que ejecuta en un solo servidor la aplicación, el servidor web y la base '
        'de datos. Esa restricción de memoria no es un dato accesorio: condiciona '
        'decisiones de diseño que se documentan más adelante, señaladamente la de '
        'mantener el entrenamiento del modelo predictivo fuera del proceso que '
        'atiende las peticiones. La Tabla 201 resume la plataforma.', a)

    filas = [['Componente', 'Versión', 'Papel en el proyecto']]
    for c, v, p in [
        ('Python', '3.12',
         'Lenguaje de programación del sistema y del componente predictivo.'),
        ('Django', '5.0',
         'Framework de aplicación web; estructura todo el sistema.'),
        ('SQLite', '3',
         'Base de datos del entorno de desarrollo; no requiere servidor.'),
        ('PostgreSQL', '16', 'Base de datos del entorno de producción.'),
        ('Gunicorn', '22',
         'Servidor de aplicación WSGI que ejecuta Django en producción con tres '
         'procesos de trabajo.'),
        ('Nginx', '1.24',
         'Servidor web de borde: atiende el puerto 80, entrega los archivos '
         'estáticos y reenvía el resto a Gunicorn.'),
        ('Ubuntu Server', '22.04 LTS',
         'Sistema operativo de la instancia de producción.'),
        ('Amazon EC2', 't3.small',
         'Servidor de producción: 2 vCPU y 2 GB de memoria.'),
        ('Git / GitHub', '—',
         'Control de versiones y repositorio remoto del proyecto.'),
        ('GitHub Actions', '—',
         'Integración y despliegue continuos hacia el servidor.'),
        ('AWS CDK (Python)', '2',
         'Definición de la infraestructura como código.'),
        ('Visual Studio Code', '—', 'Entorno de edición del código fuente.'),
    ]:
        filas.append([c, v, p])
    a = tabla(filas, 201, 'Plataforma y entorno de desarrollo del sistema', a,
              anchos=[Emu(int(1.5 * P)), Emu(int(0.8 * P)), Emu(int(4.0 * P))])

    a = F.titulo(doc, '4.1.2 Tecnologías y arquitecturas', 3, a)
    a = F.titulo(doc, '4.1.2.1 Arquitectura de la aplicación', 4, a)
    a = F.parrafo(
        doc,
        'El sistema se construyó sobre el patrón modelo-vista-plantilla que '
        'propone Django, que es la variante del modelo-vista-controlador en la '
        'que el framework asume el papel del controlador y el desarrollador '
        'escribe el modelo, la vista y la plantilla. Sobre ese patrón se dispuso '
        'la separación en capas descrita en la sección 3.1.2.1: la capa de '
        'presentación comprende las plantillas y los formularios; la capa de '
        'dominio concentra las reglas de negocio en módulos independientes de la '
        'interfaz; la capa de acceso a datos corresponde a los modelos y al '
        'mapeador objeto-relacional.', a)
    a = F.parrafo(
        doc,
        'La decisión de diseño con mayor consecuencia práctica fue extraer de las '
        'vistas dos criterios de negocio y concentrarlos en módulos propios. El '
        'primero es la disponibilidad efectiva de la clínica, que reside en el '
        'módulo agenda/disponibilidad.py; el segundo es la estimación de '
        'duraciones, que reside en inteligencia/servicio.py. Tres partes del '
        'sistema necesitan saber si un espacio está libre —la validación al '
        'programar una cita, la recomendación de bloques sobre el calendario y el '
        'indicador de utilización de la agenda— y mientras cada una resolvía esa '
        'pregunta por su cuenta, bastaba modificar una para que las tres dejaran '
        'de coincidir. Al concentrar el criterio en un módulo, las tres lo '
        'consultan y el sistema responde con un solo criterio.', a)

    a = F.titulo(doc, '4.1.2.2 Bibliotecas y componentes incorporados', 4, a)
    a = F.parrafo(
        doc,
        'La Tabla 202 relaciona cada biblioteca incorporada al sistema con la '
        'función que cumple y con la razón por la que fue seleccionada frente a '
        'las alternativas consideradas. El criterio general de selección fue la '
        'parsimonia: cada dependencia añadida es un componente que debe '
        'instalarse, actualizarse y mantenerse compatible en un servidor de dos '
        'gigabytes de memoria, de modo que solo se incorporó aquello que resolvía '
        'un problema que el framework no resolvía por sí mismo.', a)

    filas = [['Biblioteca', 'Versión', 'Para qué se utilizó',
              'Por qué se seleccionó']]
    for n, v, uso, razon in [
        ('Django', '5.0',
         'Estructura completa de la aplicación: enrutamiento, mapeador '
         'objeto-relacional, migraciones de esquema, sistema de autenticación, '
         'sesiones, validación de formularios, motor de plantillas y sitio de '
         'administración.',
         'Frente a un microframework como Flask, Django aporta ya construidos el '
         'sistema de autenticación, el modelo de usuario extensible, las '
         'migraciones y las protecciones contra los ataques web comunes. '
         'Reimplementar esos componentes habría consumido el tiempo del proyecto '
         'sin aportar al objeto de la investigación, que es el modelo '
         'predictivo.'),
        ('Gunicorn', '22.0',
         'Servidor de aplicación que ejecuta el proyecto en producción con tres '
         'procesos de trabajo.',
         'El servidor de desarrollo de Django es de un solo hilo y su propia '
         'documentación advierte que no debe usarse en producción. Gunicorn es el '
         'servidor WSGI de uso más extendido en el ecosistema de Python y se '
         'administra como un servicio del sistema operativo.'),
        ('WhiteNoise', '6.6',
         'Entrega de los archivos estáticos —hojas de estilo, scripts e '
         'imágenes— desde el propio proceso de la aplicación, con compresión y '
         'nombres versionados por contenido.',
         'La alternativa habitual es un servicio de almacenamiento con red de '
         'distribución de contenido, que para una clínica con cinco usuarios '
         'concurrentes añadiría costo mensual y una dependencia externa sin '
         'beneficio perceptible. WhiteNoise resuelve el mismo problema sin '
         'infraestructura adicional.'),
        ('psycopg2-binary', '2.9',
         'Controlador de conexión entre Django y PostgreSQL en producción.',
         'Es el controlador que la documentación de Django recomienda para '
         'PostgreSQL. Se eligió la distribución binaria porque no requiere '
         'compilar código nativo en el servidor, lo que en una instancia de dos '
         'gigabytes evita instalar un compilador completo.'),
        ('python-dotenv', '1.0',
         'Carga de las variables de entorno desde el archivo local de '
         'configuración.',
         'El servicio del sistema operativo recibe sus variables de un archivo '
         'de entorno, pero los comandos administrativos ejecutados a mano no las '
         'recibirían. Con esta biblioteca el servidor y los comandos leen la '
         'misma configuración, de modo que una migración ejecutada manualmente '
         'no se aplique por error sobre otra base de datos.'),
        ('scikit-learn', '1.4',
         'Construcción, entrenamiento y evaluación del modelo predictivo: '
         'codificación de las variables categóricas, regresión lineal múltiple, '
         'bosque aleatorio, partición del conjunto en entrenamiento y prueba, y '
         'cálculo de las métricas de error.',
         'Es la biblioteca de referencia para aprendizaje automático clásico en '
         'Python y la que implementa los algoritmos que el marco teórico de este '
         'trabajo describe. Su aporte decisivo es la tubería de procesamiento, '
         'que serializa el preprocesamiento junto con el estimador: así el '
         'proceso web no puede aplicar una codificación distinta de la del '
         'entrenamiento, que es una de las fuentes de error más frecuentes al '
         'poner un modelo en producción.'),
        ('pandas', '2.2',
         'Construcción de la tabla de datos con que se entrena el modelo y del '
         'registro individual con que se solicita cada predicción.',
         'El transformador de columnas de scikit-learn selecciona las variables '
         'por nombre, lo que exige una estructura tabular con encabezados. '
         'Resolverlo con arreglos de NumPy obligaría a mantener a mano el mismo '
         'orden de columnas en el entrenamiento y en la predicción, con el '
         'riesgo de que una variable se desplace y el modelo prediga sobre datos '
         'equivocados sin informar error alguno.'),
        ('joblib', '1.3',
         'Serialización del modelo entrenado a un archivo en disco y lectura de '
         'ese archivo por el proceso web.',
         'Es el mecanismo que la documentación de scikit-learn recomienda para '
         'persistir modelos, porque almacena los arreglos numéricos de forma más '
         'eficiente que el módulo estándar de serialización de Python. Se emplea '
         'con compresión de nivel tres, que reduce el archivo del bosque '
         'aleatorio a poco más de medio megabyte.'),
        ('Bootstrap', '5.3.3',
         'Sistema de rejilla responsiva y componentes de interfaz: formularios, '
         'tablas, tarjetas, alertas, menús desplegables y distintivos de estado.',
         'Permite que las pantallas se adapten a distintos tamaños de ventana '
         'sin escribir un sistema de estilos propio. Frente a alternativas como '
         'Tailwind CSS, no requiere un paso de compilación de los estilos, lo que '
         'mantiene el despliegue reducido a actualizar el código de Python y las '
         'plantillas.'),
        ('Bootstrap Icons', '1.11.3',
         'Iconografía de la navegación, de los botones y de los estados.',
         'Es el conjunto de iconos del mismo proyecto que el sistema de estilos, '
         'de modo que la apariencia resulta consistente y no se añade un segundo '
         'origen de recursos externos.'),
        ('Chart.js', '4.4.1',
         'Dibujo de las gráficas del módulo de reportes y del panel del modelo '
         'predictivo sobre un lienzo del navegador.',
         'Las gráficas se dibujan en el navegador del usuario y no en el '
         'servidor. Generarlas en el servidor con una biblioteca como Matplotlib '
         'consumiría memoria de la instancia en cada consulta y produciría '
         'imágenes fijas, sin la lectura de valores al pasar el cursor que la '
         'interpretación de los reportes requiere.'),
    ]:
        filas.append([n, v, uso, razon])
    a = tabla(filas, 202,
              'Bibliotecas incorporadas al sistema, su función y la '
              'justificación de su selección', a,
              anchos=[Emu(int(0.95 * P)), Emu(int(0.55 * P)),
                      Emu(int(2.2 * P)), Emu(int(2.6 * P))])

    a = F.parrafo(
        doc,
        'Las tres bibliotecas del componente predictivo —scikit-learn, pandas y '
        'joblib— se declaran en el archivo de requerimientos, pero se importan '
        'únicamente dentro de las funciones que las necesitan y no al inicio de '
        'los módulos. La razón es la memoria del servidor: importar esas tres '
        'bibliotecas eleva el consumo del proceso que lo haga de 44 a 182 '
        'megabytes, según la medición realizada sobre el conjunto de datos del '
        'sistema. Con tres procesos de trabajo de Gunicorn y una base de datos '
        'PostgreSQL en la misma instancia de dos gigabytes, cargarlas al arrancar '
        'cada proceso consumiría memoria incluso en las peticiones que no estiman '
        'nada. La importación diferida mantiene ese costo acotado al momento en '
        'que efectivamente se predice y, una vez leído, el modelo se conserva en '
        'memoria para las peticiones siguientes.', a)
    a = F.parrafo(
        doc,
        'Se consideró además la biblioteca XGBoost, mencionada en las preguntas '
        'auxiliares de la investigación como algoritmo candidato. Se decidió no '
        'incorporarla al sistema por dos razones. La primera es que introduce una '
        'dependencia con código nativo compilado, más pesada de instalar y de '
        'mantener en la instancia de producción. La segunda es que, sobre el '
        'conjunto de datos disponible, el bosque aleatorio alcanzó un coeficiente '
        'de determinación de 0.945, de modo que el margen de mejora que podría '
        'aportar un algoritmo de potenciación del gradiente no justificaba el '
        'costo de la dependencia. La comparación entre los dos algoritmos '
        'efectivamente implementados se presenta en la sección 4.2.3.10.', a)

    a = F.titulo(doc, '4.1.2.3 Herramientas de apoyo al desarrollo y a la '
                      'documentación', 4, a)
    a = F.parrafo(
        doc,
        'Un segundo grupo de herramientas no forma parte del sistema desplegado, '
        'pero intervino en su construcción y en la elaboración de este '
        'documento. Se declaran por transparencia metodológica: los diagramas y '
        'las capturas que ilustran el trabajo no se dibujaron a mano ni se '
        'recortaron de la pantalla, sino que se generaron a partir del código '
        'fuente, de modo que reflejen el sistema tal como está construido y '
        'puedan regenerarse cuando el sistema cambie. La Tabla 203 las '
        'relaciona.', a)

    filas = [['Herramienta', 'Para qué se utilizó', 'Por qué se seleccionó']]
    for n, uso, razon in [
        ('PlantUML',
         'Generación de los diagramas de actividad de los dieciséis procesos, de '
         'los diagramas de casos de uso y del diagrama de clases.',
         'Los diagramas se escriben como texto y se versionan junto con el '
         'código fuente, de modo que un cambio en un proceso se refleje '
         'regenerando el diagrama y no redibujándolo.'),
        ('Graphviz',
         'Generación del diagrama entidad-relación agrupado por módulo.',
         'Dispone automáticamente veinticuatro entidades y veintinueve '
         'relaciones con agrupación por subgrafos, lo que resultó legible donde '
         'una disposición automática sin agrupar no lo era.'),
        ('Matplotlib',
         'Generación del diagrama de arquitectura de software por capas.',
         'Permite construir el diagrama por programa, con las mismas '
         'proporciones y la misma paleta del resto de las ilustraciones.'),
        ('Playwright y Chromium',
         'Captura automatizada de las veintiséis pantallas del sistema que '
         'ilustran el capítulo 3 y el presente capítulo.',
         'Las capturas se toman todas con el mismo ancho de ventana y el mismo '
         'factor de escala, sobre el mismo conjunto de datos de demostración, de '
         'modo que las figuras del documento resulten comparables entre sí.'),
        ('python-docx',
         'Composición de este documento: inserción de secciones, tablas, '
         'figuras y pies con el formato establecido.',
         'Permite que el diccionario de datos, los requerimientos y las '
         'especificaciones se generen desde su origen —los modelos del '
         'sistema— y no se transcriban a mano, con lo que el documento no se '
         'desactualiza respecto del código.'),
    ]:
        filas.append([n, uso, razon])
    a = tabla(filas, 203,
              'Herramientas de apoyo al desarrollo y a la documentación del '
              'proyecto', a,
              anchos=[Emu(int(1.2 * P)), Emu(int(2.4 * P)), Emu(int(2.7 * P))])

    a = F.titulo(doc, '4.1.2.4 Organización del código fuente', 4, a)
    a = F.parrafo(
        doc,
        'El repositorio del proyecto se organiza en cuatro directorios de primer '
        'nivel: app contiene el proyecto Django; infra, la definición de la '
        'infraestructura como código; ml, los artefactos del entrenamiento del '
        'modelo; y docs, la documentación y las entregas. Dentro de app, cada '
        'módulo funcional del sistema corresponde a una aplicación de Django con '
        'sus propios modelos, vistas, formularios, direcciones y plantillas. Esa '
        'correspondencia entre módulo y aplicación es deliberada: permite que el '
        'código de un módulo se lea, se pruebe y se modifique sin abrir los '
        'demás. La Tabla 204 relaciona cada aplicación con su responsabilidad y '
        'con su tamaño aproximado en líneas de código.', a)

    filas = [['Aplicación', 'Responsabilidad', 'Archivos principales', 'Líneas']]
    for n, r, arch, l in [
        ('config',
         'Configuración del proyecto, enrutamiento raíz, validadores '
         'compartidos y formatos regionales.',
         'settings.py, urls.py, validadores.py, formats/es/formats.py', '≈ 290'),
        ('usuarios',
         'Autenticación, roles y control de acceso; mantenimiento de usuarios, '
         'recuperación de contraseña y auditoría.',
         'models.py, views.py, forms.py, backends.py, decorators.py, '
         'middleware.py, context_processors.py', '≈ 660'),
        ('pacientes',
         'Registro de pacientes, antecedentes médicos e historial de cambios.',
         'models.py, views.py, forms.py', '≈ 300'),
        ('catalogo',
         'Especialidades, procedimientos, odontólogos y unidades dentales.',
         'models.py, views.py, forms.py', '≈ 400'),
        ('agenda',
         'Módulo Principal: calendario, programación de citas, horarios, '
         'ausencias y registro de tiempos reales. Incluye el módulo de '
         'disponibilidad efectiva.',
         'views.py, forms.py, models.py, disponibilidad.py', '≈ 1,335'),
        ('clinico',
         'Expediente clínico con odontograma, notas de evolución, planes de '
         'tratamiento por fases y cobros.',
         'models.py, views.py, forms.py, piezas.py', '≈ 1,345'),
        ('inteligencia',
         'Servicio de estimación de duraciones, entrenamiento y versionado del '
         'modelo predictivo.',
         'servicio.py, entrenamiento.py, models.py, views.py, '
         'management/commands/entrenar.py', '≈ 710'),
        ('reportes',
         'Indicadores operativos y reportes de precisión de la estimación.',
         'servicio.py, views.py, models.py', '≈ 230'),
    ]:
        filas.append([n, r, arch, l])
    a = tabla(filas, 204,
              'Organización del código fuente por aplicación del proyecto', a,
              anchos=[Emu(int(0.9 * P)), Emu(int(2.2 * P)),
                      Emu(int(2.6 * P)), Emu(int(0.6 * P))])

    a = F.parrafo(
        doc,
        'El código fuente se escribió siguiendo cuatro convenciones constantes. '
        'La primera es que los identificadores están en español —nombres de '
        'modelos, de campos, de funciones y de variables—, salvo los que el '
        'framework impone, con lo que el vocabulario del código coincide con el '
        'de la clínica y con el de este documento. La segunda es el borrado '
        'lógico: ninguna entidad se elimina de la base de datos, sino que se '
        'marca con el campo estado en falso, de modo que un procedimiento dado '
        'de baja conserve su vínculo con las citas históricas que lo utilizaron. '
        'La tercera es que toda modificación de un registro sensible deja '
        'constancia en una tabla de historial, con el estado anterior y el '
        'usuario que la realizó. La cuarta es que cada módulo y cada función no '
        'evidente llevan una cadena de documentación que explica no lo que hace '
        'el código, que se lee en el código, sino por qué está escrito así, con '
        'lo que las decisiones de diseño quedan registradas donde se aplican.', a)

    a = F.titulo(doc, '4.1.3 Seguridad', 3, a)
    a = F.parrafo(
        doc,
        'El sistema administra información de salud de pacientes identificados, '
        'de modo que la seguridad no se limita a controlar quién entra. Se '
        'implementó en cinco planos: la autenticación, que establece quién es el '
        'usuario; la autorización, que determina qué puede hacer; la protección '
        'de la sesión; la protección de los datos frente a los ataques web '
        'habituales; y la gestión de los secretos de configuración.', a)

    a = F.titulo(doc, '4.1.3.1 Autenticación', 4, a)
    a = F.parrafo(
        doc,
        'La identificación del usuario se realiza con su correo electrónico, que '
        'el modelo declara como campo único, en lugar del nombre de usuario que '
        'Django emplea por omisión. Para ello se implementó un respaldo de '
        'autenticación propio, que localiza al usuario por correo sin distinguir '
        'mayúsculas y delega en el framework la verificación de la contraseña y '
        'del estado de la cuenta.', a)
    a = F.parrafo(
        doc,
        'Las contraseñas nunca se almacenan: la base de datos guarda el resumen '
        'criptográfico que produce el algoritmo PBKDF2 con función de resumen '
        'SHA-256 y 720,000 iteraciones, que es el mecanismo predeterminado de '
        'Django 5. El número de iteraciones es lo que encarece deliberadamente '
        'cada intento de adivinación por fuerza bruta. Además, toda contraseña '
        'nueva debe superar los cuatro validadores del framework: longitud '
        'mínima, disimilitud respecto de los datos del propio usuario, ausencia '
        'de la lista de contraseñas comunes y prohibición de contraseñas '
        'enteramente numéricas.', a)
    a = F.parrafo(
        doc,
        'El respaldo de autenticación incorpora una precaución que no es '
        'evidente en su lectura. Cuando el correo no existe, en lugar de '
        'responder de inmediato, calcula el resumen de la contraseña recibida y '
        'lo descarta. Sin esa operación, un correo inexistente se rechazaría de '
        'inmediato y uno existente con contraseña equivocada tardaría el tiempo '
        'del cálculo del resumen, con lo que la diferencia de tiempos de '
        'respuesta permitiría averiguar qué correos están registrados en el '
        'sistema.', a)
    a = F.parrafo(
        doc,
        'La recuperación de contraseña se resuelve con una pregunta secreta '
        'elegida de una lista cerrada al dar de alta la cuenta. La respuesta '
        'tampoco se almacena en claro: se normaliza a minúsculas y se guarda con '
        'el mismo algoritmo de resumen que las contraseñas. El proceso se divide '
        'en tres pasos y cada uno verifica en la sesión que el anterior se haya '
        'completado, de modo que no sea posible llegar a la pantalla de '
        'definición de la nueva contraseña sin haber respondido correctamente.', a)

    a = F.titulo(doc, '4.1.3.2 Autorización y control de acceso por rol', 4, a)
    a = F.parrafo(
        doc,
        'El control de acceso se implementó como un modelo basado en roles. Cada '
        'rol declara, con un campo booleano por módulo, a cuáles de los ocho '
        'módulos del sistema tiene acceso, y dos campos adicionales matizan ese '
        'acceso. El campo de solo consulta distingue entre ver y modificar: un '
        'rol puede tener acceso a un módulo y, sin embargo, no poder crear ni '
        'alterar registros en él. El campo de escritura clínica se declara '
        'aparte porque el expediente responde a una lógica distinta de la '
        'administrativa: quien lo escribe es el profesional con competencia para '
        'hacerlo, aunque su rol sea de solo consulta para la agenda de la '
        'clínica, y no lo escribe la recepción, aunque sí modifique otros '
        'módulos. Derivar ese permiso del campo de solo consulta habría dado el '
        'resultado contrario en los dos casos.', a)
    a = F.parrafo(
        doc,
        'La restricción se aplica en la vista, no en la plantilla. Cada vista '
        'lleva un decorador que exige acceso al módulo y, cuando modifica '
        'información, que exige además permiso de escritura; si no se cumplen, '
        'la petición se rechaza antes de ejecutar la vista. Ocultar el botón en '
        'la pantalla es una comodidad de la interfaz, no una medida de '
        'seguridad: un usuario que escriba la dirección a mano llegaría '
        'igualmente a la vista. Para que la interfaz y la seguridad no se '
        'contradigan, un procesador de contexto pone a disposición de todas las '
        'plantillas el mismo cálculo de permisos que aplica el decorador, de '
        'modo que el menú y los botones se construyan a partir de la misma '
        'fuente que autoriza.', a)

    a = F.titulo(doc, '4.1.3.3 Protección de la sesión y del navegador', 4, a)
    a = F.parrafo(
        doc,
        'La sesión se mantiene con la cookie de sesión de Django, marcada como '
        'inaccesible al código JavaScript de la página, de modo que una '
        'inyección de script no pueda leer el identificador de sesión y '
        'suplantar al usuario. Todos los formularios que modifican información '
        'incorporan el testigo contra falsificación de petición entre sitios que '
        'el framework verifica en el servidor, con lo que una página externa no '
        'puede provocar una acción en nombre de un usuario con sesión abierta. '
        'El encabezado que prohíbe mostrar el sistema dentro de un marco está '
        'fijado en denegar, lo que impide el ataque de superposición de '
        'interfaces.', a)
    a = F.parrafo(
        doc,
        'Se agregó además un componente intermedio propio que impide al '
        'navegador almacenar en caché las páginas dinámicas. Sin él, un usuario '
        'que cierra su sesión en la computadora compartida de la recepción y '
        'pulsa el botón de retroceso del navegador vería de nuevo la página con '
        'los datos del paciente, servida desde la caché local aunque la sesión '
        'ya no exista en el servidor. El componente excluye deliberadamente los '
        'archivos estáticos, que sí deben poder almacenarse.', a)

    a = F.titulo(doc, '4.1.3.4 Protección de los datos', 4, a)
    a = F.parrafo(
        doc,
        'Todo acceso a la base de datos se realiza a través del mapeador '
        'objeto-relacional, que construye las consultas con parámetros '
        'enlazados; el sistema no concatena en ningún punto datos del usuario '
        'dentro de una sentencia SQL, que es el mecanismo del que depende la '
        'inyección de código SQL. En la salida, el motor de plantillas de Django '
        'escapa por omisión todo valor que se interpola, de modo que un dato '
        'guardado con etiquetas HTML se muestre como texto y no se ejecute en el '
        'navegador de quien lo consulta.', a)
    a = F.parrafo(
        doc,
        'La entrada se valida en el servidor y no solo en el navegador. Los '
        'validadores de nombres, correos, códigos y teléfonos están '
        'centralizados en un módulo compartido, de manera que el criterio con '
        'que se valida el nombre de un usuario sea el mismo con que se valida el '
        'de un paciente. A esa validación se añade la de las reglas de negocio '
        'en los formularios: que una cita no se programe en el pasado, que quepa '
        'en la disponibilidad efectiva del profesional, que no se traslape con '
        'otra y que quede una unidad dental libre. Esas reglas no son '
        'validaciones de formato, pero su lugar es el mismo, porque un dato que '
        'las incumple corrompe la operación igual que un dato mal escrito.', a)
    a = F.parrafo(
        doc,
        'La integridad histórica se protege por dos vías complementarias. La '
        'primera es el borrado lógico ya descrito. La segunda son las tablas de '
        'historial de usuarios, pacientes, citas y planes, que conservan el '
        'estado anterior, la acción realizada, el usuario responsable y la fecha. '
        'Esas tablas no referencian con llave foránea al registro que describen, '
        'sino que guardan su identificador y una copia de sus datos visibles, de '
        'modo que el historial sobreviva a la desaparición del registro original '
        'y la auditoría no quede incompleta. La Tabla 205 resume la '
        'correspondencia entre cada riesgo considerado y el mecanismo que lo '
        'atiende, con indicación del lugar del código donde está implementado.', a)

    filas = [['Riesgo', 'Mecanismo implementado', 'Dónde está implementado']]
    for r, m, d in [
        ('Robo de contraseñas desde la base de datos',
         'Resumen criptográfico PBKDF2-SHA256 con 720,000 iteraciones; la '
         'contraseña nunca se almacena.',
         'Mecanismo predeterminado de Django; modelo Usuario'),
        ('Contraseñas débiles',
         'Cuatro validadores obligatorios: longitud, disimilitud, lista de '
         'contraseñas comunes y prohibición de valores numéricos.',
         'config/settings.py (AUTH_PASSWORD_VALIDATORS)'),
        ('Enumeración de cuentas por tiempo de respuesta',
         'El respaldo de autenticación calcula un resumen incluso cuando el '
         'correo no existe, para igualar el tiempo de respuesta.',
         'usuarios/backends.py'),
        ('Acceso a un módulo sin autorización',
         'Decorador que exige el permiso del rol antes de ejecutar la vista.',
         'usuarios/decorators.py (modulo_requerido)'),
        ('Modificación de datos por un rol de solo consulta',
         'Decorador de escritura que verifica el permiso en la vista y no en la '
         'plantilla.',
         'usuarios/decorators.py (escritura_requerida)'),
        ('Escritura del expediente clínico por personal no facultado',
         'Permiso de escritura clínica declarado por separado del permiso '
         'administrativo.',
         'usuarios/models.py (Rol.escritura_clinica)'),
        ('Inyección de código SQL',
         'Consultas construidas por el mapeador objeto-relacional con '
         'parámetros enlazados; sin concatenación de entradas.',
         'Todo el acceso a datos del sistema'),
        ('Ejecución de scripts inyectados (XSS)',
         'Escape automático de todo valor interpolado en las plantillas.',
         'Motor de plantillas de Django'),
        ('Falsificación de petición entre sitios (CSRF)',
         'Testigo por formulario, verificado en el servidor en toda petición que '
         'modifica información.',
         'CsrfViewMiddleware y plantillas'),
        ('Robo de la sesión desde el navegador',
         'Cookie de sesión inaccesible al código JavaScript de la página.',
         'SESSION_COOKIE_HTTPONLY'),
        ('Superposición de interfaces (clickjacking)',
         'Encabezado que prohíbe mostrar el sistema dentro de un marco.',
         'XFrameOptionsMiddleware (X_FRAME_OPTIONS = DENY)'),
        ('Lectura de datos de un paciente tras cerrar la sesión',
         'Encabezados que impiden al navegador almacenar en caché las páginas '
         'dinámicas.',
         'usuarios/middleware.py (NoCacheMiddleware)'),
        ('Pérdida de la trazabilidad de la información',
         'Borrado lógico en todas las entidades y tablas de historial con el '
         'estado anterior y el usuario responsable.',
         'Campo estado y tablas HistorialUsuario, HistorialPaciente, '
         'HistorialCita e HistorialPlan'),
        ('Exposición de credenciales en el repositorio',
         'Toda credencial se lee de variables de entorno; el archivo de entorno '
         'y las llaves están excluidos del control de versiones.',
         'config/settings.py y .gitignore'),
    ]:
        filas.append([r, m, d])
    a = tabla(filas, 205,
              'Riesgos considerados y mecanismos de seguridad implementados', a,
              anchos=[Emu(int(1.7 * P)), Emu(int(2.6 * P)), Emu(int(2.0 * P))])

    a = F.titulo(doc, '4.1.3.5 Gestión de la configuración y de los secretos', 4, a)
    a = F.parrafo(
        doc,
        'Ninguna credencial figura en el código fuente. La clave secreta de '
        'Django, la contraseña de la base de datos, los nombres de dominio '
        'autorizados y el indicador de depuración se leen de variables de '
        'entorno, con valores predeterminados aptos solo para el entorno de '
        'desarrollo. En el servidor, esas variables se entregan al servicio '
        'desde un archivo de entorno que no forma parte del repositorio, y el '
        'archivo de exclusiones del control de versiones descarta explícitamente '
        'los archivos de entorno, las llaves privadas y los certificados. Las '
        'credenciales que el flujo de despliegue continuo necesita para entrar '
        'al servidor —la dirección, el usuario y la llave privada de acceso '
        'remoto— se almacenan como secretos del repositorio en la plataforma de '
        'integración continua y se inyectan durante la ejecución, de modo que no '
        'aparecen en el archivo del flujo.', a)
    a = F.parrafo(
        doc,
        'Queda pendiente una medida de endurecimiento que se documenta por '
        'honestidad metodológica: el servidor atiende actualmente por el '
        'protocolo HTTP sin cifrar. Mientras el sistema opera con datos de '
        'demostración la exposición es acotada, pero el manejo de información '
        'clínica real exige habilitar HTTPS con un certificado y activar en '
        'consecuencia las marcas de cookie segura y de redirección obligatoria. '
        'Es la primera tarea del plan de puesta en producción definitiva.', a)

    doc.save(str(C.ARCHIVO))
    print('4.1 agregada: 5 tablas.')


if __name__ == '__main__':
    main()
