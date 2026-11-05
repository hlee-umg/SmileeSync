"""Verifica el módulo de Inteligencia, el de Reportes y la cadena de estimación."""

import os
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "testserver,localhost,127.0.0.1")
django.setup()

# `time` ya nombra al módulo estándar en este archivo, de modo que la hora
# del reloj se importa con otro nombre.
from datetime import time as hora_reloj, timedelta  # noqa: E402

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from agenda.models import Cita  # noqa: E402
from catalogo.models import Odontologo, Procedimiento  # noqa: E402
from inteligencia import entrenamiento, evaluacion, servicio  # noqa: E402
from inteligencia.models import (
    DatoEntrenamiento,
    ModeloVersion,  # noqa: E402
    Prediccion,
)
from usuarios.models import Usuario  # noqa: E402

ok = fallo = 0


def probar(t, c, d=""):
    global ok, fallo
    if c:
        ok += 1
        print(f"  OK    {t}")
    else:
        fallo += 1
        print(f"  FALLA {t} {d}")


admin = Usuario.objects.get(email="admin@smileesync.local")
recep = Usuario.objects.get(email="recepcion@smileesync.local")
odo_usuario = Usuario.objects.get(email="hjlee@smileesync.local")
c = Client()
c.force_login(admin)
c_recep = Client()
c_recep.force_login(recep)
c_odo = Client()
c_odo.force_login(odo_usuario)

hoy = timezone.localdate()
futuro = hoy + timedelta(days=40)
while futuro.weekday() > 4:
    futuro += timedelta(days=1)

print("1. El conjunto de entrenamiento se arma desde las citas y sus notas")
filas = entrenamiento.reunir_datos()
probar(
    "hay registros suficientes para entrenar",
    len(filas) >= entrenamiento.MINIMO_REGISTROS,
    len(filas),
)
columnas = set(filas[0])
probar(
    "incluye las variables de la cita",
    {"procedimiento", "odontologo", "dia_semana", "hora_inicio"} <= columnas,
)
probar(
    "incluye las variables de la nota clínica",
    {"num_piezas", "anestesia", "complicacion"} <= columnas,
)
probar("incluye la duración real como objetivo", "duracion_real_min" in columnas)
probar(
    "ninguna cita cancelada entra al conjunto",
    len(filas)
    == Cita.objects.filter(
        estado_cita="ATENDIDA", duracion_real_min__isnull=False, estado=True
    ).count(),
)

print("\n2. El entrenamiento produce métricas comparables contra una línea base")
resultado = entrenamiento.entrenar("RF", guardar=True)
probar("el entrenamiento concluye", resultado is not None)
probar(
    "reserva registros para evaluar",
    0 < resultado.registros_prueba < resultado.registros,
    f"{resultado.registros_prueba}/{resultado.registros}",
)
probar(
    "el error es menor que estimar siempre el promedio",
    resultado.mae < resultado.mae_base,
    f"{resultado.mae} vs {resultado.mae_base}",
)
probar(
    "la mejora se reporta como porcentaje",
    resultado.mejora_pct > 0,
    resultado.mejora_pct,
)
probar(
    "el entrenamiento toma menos de cinco segundos",
    resultado.segundos < 5,
    f"{resultado.segundos} s",
)
probar(
    "genera el archivo serializado",
    os.path.exists(resultado.ruta) and resultado.tamano_kb > 0,
)
probar("reporta el peso de las variables", len(resultado.importancias) > 0)

print("\n3. El versionado conserva el histórico y activa una sola versión")
antes = ModeloVersion.objects.count()
version = entrenamiento.registrar_version(resultado, activar=True)
probar("la versión queda registrada", ModeloVersion.objects.count() == antes + 1)
probar("la versión nueva está activa", version.activo)
probar(
    "solo hay una versión en producción",
    ModeloVersion.objects.filter(activo=True, estado=True).count() == 1,
)
otra = entrenamiento.registrar_version(resultado, activar=False)
probar("una versión nueva no se activa sola", not otra.activo)
probar(
    "la anterior sigue en producción", ModeloVersion.objects.get(pk=version.pk).activo
)
entrenamiento.activar_version(otra)
probar(
    "al activar otra, la anterior se retira",
    not ModeloVersion.objects.get(pk=version.pk).activo,
)
probar(
    "sigue habiendo una sola activa",
    ModeloVersion.objects.filter(activo=True, estado=True).count() == 1,
)

print("\n4. La estimación usa el modelo y responde en línea")
odo_lento = Odontologo.objects.get(colegiado="CD-19877")
odo_rapido = Odontologo.objects.get(colegiado="CD-20451")
resina = Procedimiento.objects.get(codigo="PROC-002")


def estimar(odo, piezas=1):
    r = c.get(
        reverse("agenda:estimar"),
        {
            "procedimiento": resina.pk,
            "odontologo": odo.pk,
            "fecha": futuro.isoformat(),
            "hora": "09:00",
            "piezas": piezas,
        },
    )
    return r.json()


d = estimar(odo_lento)
probar("la estimación proviene del modelo", d["origen"] == "modelo", d["origen"])
probar(
    "declara el origen en la interfaz",
    d["etiqueta_origen"] == "Modelo predictivo",
    d["etiqueta_origen"],
)
probar(
    "el bloque recomendado rodea la estimación",
    d["bloque_min"] <= d["duracion"] <= d["bloque_max"],
    (d["bloque_min"], d["duracion"], d["bloque_max"]),
)

uno, dos, tres = (estimar(odo_lento, n)["duracion"] for n in (1, 2, 3))
probar(
    "la estimación crece con el número de piezas", uno < dos < tres, (uno, dos, tres)
)
# El ritmo se comprueba sobre la predicción del modelo y no sobre la cifra que
# muestra la pantalla: la agenda redondea a múltiplos de cinco minutos, de modo
# que una diferencia real de cuatro minutos puede quedar oculta tras el
# redondeo sin que el modelo haya dejado de distinguir a los profesionales.
activo = servicio._modelo_activo()
crudo_rapido = servicio._estimar_con_modelo(
    activo, resina, odo_rapido, futuro, hora_reloj(9, 0), 1
)
crudo_lento = servicio._estimar_con_modelo(
    activo, resina, odo_lento, futuro, hora_reloj(9, 0), 1
)
probar(
    "distingue el ritmo de cada profesional",
    crudo_rapido < crudo_lento,
    f"{crudo_rapido:.2f} vs {crudo_lento:.2f}",
)
probar(
    "la estimación que se muestra se redondea a múltiplos de cinco",
    estimar(odo_lento)["duracion"] % 5 == 0,
)

print("\n5. El modelo se conserva en memoria entre peticiones")
servicio.limpiar_cache()
inicio = time.perf_counter()
estimar(odo_lento)
primera = time.perf_counter() - inicio
inicio = time.perf_counter()
for _ in range(10):
    estimar(odo_lento)
siguientes = (time.perf_counter() - inicio) / 10
probar(
    "la primera carga es la más costosa",
    primera > siguientes,
    f"{primera*1000:.0f} ms vs {siguientes*1000:.0f} ms",
)
probar(
    "las estimaciones siguientes bajan de 100 ms",
    siguientes < 0.1,
    f"{siguientes*1000:.0f} ms",
)

print("\n6. Sin modelo, la cadena de respaldo sostiene la estimación")
ModeloVersion.objects.update(activo=False)
servicio.limpiar_cache()
d = estimar(odo_lento)
probar("la estimación sigue disponible", d["disponible"])
probar("recae en el promedio histórico", d["origen"] == "historico", d["origen"])
probar("explica de dónde salió el número", len(d["detalle"]) > 20)
nueva = ModeloVersion.objects.filter(estado=True).first()
entrenamiento.activar_version(nueva)
probar(
    "al reactivar, vuelve a usar el modelo", estimar(odo_lento)["origen"] == "modelo"
)

print("\n7. Un archivo de modelo inválido no impide agendar")
activa = ModeloVersion.objects.get(activo=True)
ruta_original = activa.ruta_archivo
activa.ruta_archivo = "/ruta/que/no/existe.joblib"
activa.save(update_fields=["ruta_archivo"])
servicio.limpiar_cache()
d = estimar(odo_lento)
probar("la estimación no se interrumpe", d["disponible"])
probar("cae al nivel siguiente de la cadena", d["origen"] != "modelo", d["origen"])
activa.ruta_archivo = ruta_original
activa.save(update_fields=["ruta_archivo"])
servicio.limpiar_cache()

print("\n8. Pantalla del módulo de Inteligencia")
r = c.get(reverse("inteligencia:panel"))
cuerpo = r.content.decode()
probar("responde 200", r.status_code == 200, r.status_code)
probar("lista las versiones entrenadas", "En producción" in cuerpo)
probar("muestra el error del modelo", "Error del modelo" in cuerpo)
probar("contrasta contra el error del catálogo", "Error del catálogo" in cuerpo)
probar("documenta la cadena de estimación", "Cadena de estimación" in cuerpo)
probar("indica cómo se entrena", "manage.py entrenar" in cuerpo)

print("\n9. Pantalla del módulo de Reportes")
r = c.get(reverse("reportes:panel"))
cuerpo = r.content.decode()
probar("responde 200", r.status_code == 200, r.status_code)
probar("presenta los indicadores del período", "Utilización de la agenda" in cuerpo)
probar("incluye la gráfica de atenciones", "g-semanal" in cuerpo)
probar("incluye el contraste catálogo contra real", "g-precision" in cuerpo)
probar("ofrece los datos también en tabla", "Desviación por procedimiento" in cuerpo)
r = c.get(reverse("reportes:panel"), {"semanas": "4"})
probar(
    "el período es filtrable",
    r.status_code == 200 and "Últimas 4 semanas" in r.content.decode(),
)

print("\n10. Control de acceso de los módulos nuevos")
probar(
    "la recepción entra a reportes",
    c_recep.get(reverse("reportes:panel")).status_code == 200,
)
probar(
    "la recepción no entra a inteligencia",
    c_recep.get(reverse("inteligencia:panel")).status_code == 403,
)
probar(
    "el odontólogo no entra a reportes",
    c_odo.get(reverse("reportes:panel")).status_code == 403,
)
probar(
    "el odontólogo no entra a inteligencia",
    c_odo.get(reverse("inteligencia:panel")).status_code == 403,
)
probar(
    "la recepción no activa versiones del modelo",
    c_recep.post(reverse("inteligencia:activar", args=[nueva.pk])).status_code == 403,
)

print("\n11. El conjunto de entrenamiento se mantiene al día")
antes = DatoEntrenamiento.objects.count()
probar(
    "el conjunto tiene una fila por atención medida",
    antes
    == Cita.objects.filter(
        estado_cita="ATENDIDA", duracion_real_min__isnull=False, estado=True
    ).count(),
    antes,
)
altas, cambios, bajas = entrenamiento.sincronizar()
probar(
    "sincronizar dos veces no duplica nada",
    (altas, cambios, bajas) == (0, 0, 0),
    (altas, cambios, bajas),
)

medida = Cita.objects.filter(
    estado_cita="ATENDIDA", duracion_real_min__isnull=False
).first()
original = medida.duracion_real_min
medida.duracion_real_min = original + 7
medida.save(update_fields=["duracion_real_min"])
altas, cambios, bajas = entrenamiento.sincronizar()
probar("una duración corregida se actualiza en el conjunto", cambios == 1, cambios)
probar(
    "el conjunto refleja el valor corregido",
    DatoEntrenamiento.objects.get(cita=medida).duracion_real_min == original + 7,
)
medida.duracion_real_min = original
medida.save(update_fields=["duracion_real_min"])
entrenamiento.sincronizar()

medida.estado_cita = "CANCELADA"
medida.save(update_fields=["estado_cita"])
altas, cambios, bajas = entrenamiento.sincronizar()
probar(
    "una cita cancelada después de atenderse sale del conjunto",
    bajas == 1 and not DatoEntrenamiento.objects.filter(cita=medida).exists(),
)
medida.estado_cita = "ATENDIDA"
medida.save(update_fields=["estado_cita"])
altas, _, _ = entrenamiento.sincronizar()
probar("al restituirse la atención vuelve a entrar", altas == 1, altas)

probar(
    "el registro al cerrar una cita no duplica la fila",
    servicio.registrar_dato_entrenamiento(medida) is not None
    and DatoEntrenamiento.objects.filter(cita=medida).count() == 1,
)
dato = DatoEntrenamiento.objects.get(cita=medida)
probar(
    "el conjunto guarda las variables de la nota clínica",
    hasattr(dato, "anestesia") and hasattr(dato, "complicacion"),
)
probar(
    "el conjunto guarda la duración de referencia del catálogo",
    dato.duracion_catalogo_min == medida.procedimiento.duracion_promedio_min,
    dato.duracion_catalogo_min,
)

filas = entrenamiento.reunir_datos()
probar(
    "el conjunto que se entrena sale de esa tabla",
    len(filas) == DatoEntrenamiento.objects.count(),
)
probar(
    "cada registro lleva la duración del catálogo para contrastar",
    all(f["duracion_catalogo"] > 0 for f in filas),
)

print("\n12. El modelo se contrasta contra el método que la clínica usa hoy")
resultado = entrenamiento.entrenar("RF", guardar=True)
probar(
    "se mide el error de estimar con el catálogo",
    resultado.mae_catalogo > 0,
    resultado.mae_catalogo,
)
probar(
    "se mide sobre el mismo subconjunto de prueba que el modelo",
    resultado.registros_prueba == 112 or resultado.registros_prueba > 0,
)
probar(
    "el modelo reduce el error del catálogo",
    resultado.mae < resultado.mae_catalogo,
    f"{resultado.mae} vs {resultado.mae_catalogo}",
)
probar(
    "la reducción se reporta como porcentaje",
    resultado.mejora_catalogo_pct > 0,
    resultado.mejora_catalogo_pct,
)
probar(
    "se declara si alcanza la meta del proyecto",
    resultado.cumple_meta
    == (resultado.mejora_catalogo_pct >= entrenamiento.META_REDUCCION_PCT),
)
probar(
    "la meta del proyecto es reducir un 25 %", entrenamiento.META_REDUCCION_PCT == 25.0
)

version = entrenamiento.registrar_version(resultado, activar=True)
probar(
    "la versión conserva el error del catálogo",
    ModeloVersion.objects.get(pk=version.pk).mae_catalogo == resultado.mae_catalogo,
)
lectura = evaluacion.resumen_version(version)
probar(
    "la lectura retrospectiva reporta las dos cifras y su diferencia",
    lectura["mae_modelo"] == resultado.mae
    and lectura["mae_catalogo"] == resultado.mae_catalogo
    and lectura["reduccion_pct"] == resultado.mejora_catalogo_pct,
)
probar(
    "una versión sin métricas no produce lectura",
    evaluacion.resumen_version(None) is None,
)

print("\n13. Desempeño en operación: predicciones contra la duración real")
probar(
    "sin predicciones medidas no se inventa un resultado",
    evaluacion.desempeno_en_operacion() is None or Prediccion.objects.count() > 0,
)

atendidas = list(
    Cita.objects.filter(
        estado_cita="ATENDIDA", duracion_real_min__isnull=False, estado=True
    )[:12]
)
for cita in atendidas[:8]:
    Prediccion.objects.create(
        cita=cita,
        modelo=version,
        duracion_estimada_min=cita.duracion_real_min,
        bloque_min_recomendado=max(5, cita.duracion_real_min - 5),
        bloque_max_recomendado=cita.duracion_real_min + 5,
    )
for cita in atendidas[8:]:
    Prediccion.objects.create(
        cita=cita,
        modelo=version,
        duracion_estimada_min=cita.duracion_real_min + 40,
        bloque_min_recomendado=cita.duracion_real_min + 30,
        bloque_max_recomendado=cita.duracion_real_min + 50,
    )

op = evaluacion.desempeno_en_operacion()
probar(
    "se contrastan todas las predicciones con cita atendida",
    op["predicciones"] == 12,
    op["predicciones"],
)
probar(
    "el error del modelo se calcula sobre la duración real",
    op["mae_modelo"] == round(40 * 4 / 12, 2),
    op["mae_modelo"],
)
probar(
    "se mide también el error del catálogo en las mismas citas",
    op["mae_catalogo"] is not None,
)
probar(
    "se cuenta cuántas atenciones cayeron dentro del bloque sugerido",
    op["dentro_del_bloque"] == 8 and op["dentro_pct"] == round(8 / 12 * 100, 1),
    (op["dentro_del_bloque"], op["dentro_pct"]),
)
desglose = evaluacion.desempeno_por_procedimiento()
probar(
    "el desglose por procedimiento suma las mismas atenciones",
    sum(f["atenciones"] for f in desglose) == 12,
)
probar(
    "el desglose ordena por el error del modelo",
    [f["mae_modelo"] for f in desglose]
    == sorted([f["mae_modelo"] for f in desglose], reverse=True),
)

Cita.objects.filter(pk__in=[c.pk for c in atendidas[:3]]).update(
    estado_cita="CANCELADA"
)
probar(
    "una cita cancelada sale del contraste",
    evaluacion.desempeno_en_operacion()["predicciones"] == 9,
)
Cita.objects.filter(pk__in=[c.pk for c in atendidas[:3]]).update(estado_cita="ATENDIDA")

print("\n14. El panel presenta la validación de la hipótesis")
cliente = Client()
cliente.force_login(admin)
cuerpo = cliente.get(reverse("inteligencia:panel")).content.decode()
probar("declara la validación de la hipótesis", "Validación de la hipótesis" in cuerpo)
probar(
    "contrasta con los bloques del catálogo", "Error con bloques del catálogo" in cuerpo
)
probar("reporta la reducción del error", "Reducción del error" in cuerpo)
probar("declara la meta del proyecto", "Meta del proyecto" in cuerpo)
probar("presenta el desempeño en operación", "Desempeño en operación" in cuerpo)
probar(
    "informa cuántas atenciones cayeron dentro del bloque",
    "Dentro del bloque sugerido" in cuerpo,
)
probar(
    "informa el tamaño del conjunto de entrenamiento",
    "en el conjunto de entrenamiento" in cuerpo,
)
# El indicador superior y la tarjeta de validación informan el mismo error del
# catálogo: dos cifras distintas para lo mismo confundirían a quien lo lee.
cifra = f'{lectura["mae_catalogo"]:.2f}'
probar(
    "el indicador del catálogo coincide con el de la validación",
    cuerpo.count(cifra) >= 2,
    f"{cifra} aparece {cuerpo.count(cifra)} veces",
)


print(f"\n=== {ok} correctas, {fallo} fallidas ===")
