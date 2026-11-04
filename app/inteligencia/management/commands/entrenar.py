"""Entrena una versión del modelo de estimación de duraciones.

Se ejecuta fuera del servidor web, normalmente desde una tarea programada:

    python manage.py entrenar --algoritmo RF --activar

Mantenerlo aquí y no en una vista evita cargar scikit-learn y pandas en los
procesos que atienden peticiones, que es el costo real de este componente:
alrededor de 170 MB de memoria por proceso frente a menos de un segundo de
cómputo.
"""

from django.core.management.base import BaseCommand

from inteligencia import entrenamiento


class Command(BaseCommand):
    help = (
        "Entrena el modelo de estimación de duraciones y registra la "
        "versión resultante con sus métricas."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--algoritmo",
            default="RF",
            choices=sorted(entrenamiento.ALGORITMOS),
            help="Algoritmo a entrenar (por omisión, RF).",
        )
        parser.add_argument(
            "--activar",
            action="store_true",
            help="Pone la versión entrenada en producción.",
        )
        parser.add_argument(
            "--solo-si-mejora",
            action="store_true",
            help="Activa la versión únicamente si su error "
            "absoluto medio es menor que el de la versión "
            "actualmente en producción.",
        )

    def handle(self, *args, **opciones):
        algoritmo = opciones["algoritmo"]

        altas, cambios, bajas = entrenamiento.sincronizar()
        self.stdout.write(
            f"Conjunto de entrenamiento: {altas} altas, {cambios} "
            f"actualizaciones, {bajas} bajas."
        )

        self.stdout.write(f"Entrenando {entrenamiento.ALGORITMOS[algoritmo]}…")

        resultado = entrenamiento.entrenar(algoritmo)
        if resultado is None:
            self.stdout.write(
                self.style.WARNING(
                    f"No hay registros suficientes: se requieren al menos "
                    f"{entrenamiento.MINIMO_REGISTROS} atenciones con duración real. "
                    f"La estimación sigue recayendo en el promedio histórico."
                )
            )
            return

        self.stdout.write(
            f"  Registros            {resultado.registros} "
            f"({resultado.registros_prueba} reservados para evaluación)\n"
            f"  Entrenamiento        {resultado.segundos * 1000:.0f} ms\n"
            f"  Error absoluto medio {resultado.mae} min\n"
            f"  RMSE                 {resultado.rmse} min\n"
            f"  R²                   {resultado.r2}\n"
            f"  Línea base           {resultado.mae_base} min "
            f"(estimar siempre el promedio)\n"
            f"  Mejora               {resultado.mejora_pct}%\n"
            f"  Archivo              {resultado.tamano_kb} KB"
        )

        meta = self.style.SUCCESS if resultado.cumple_meta else self.style.WARNING
        self.stdout.write(
            meta(
                f"  Catálogo             {resultado.mae_catalogo} min "
                f"(reservar el bloque de referencia)\n"
                f"  Reducción            {resultado.mejora_catalogo_pct}% frente al "
                f"catálogo; la meta del proyecto es "
                f"{entrenamiento.META_REDUCCION_PCT:.0f}%."
            )
        )

        from inteligencia.models import ModeloVersion

        activa = ModeloVersion.objects.filter(activo=True, estado=True).first()

        activar = opciones["activar"]
        if opciones["solo_si_mejora"]:
            if activa and activa.mae is not None and resultado.mae >= activa.mae:
                activar = False
                self.stdout.write(
                    self.style.WARNING(
                        f"  La versión en producción tiene un error de "
                        f"{activa.mae} min; "
                        f"la nueva no mejora y se conserva como histórico."
                    )
                )
            else:
                activar = True

        version = entrenamiento.registrar_version(resultado, activar=activar)
        estado = "activada en producción" if activar else "registrada como histórico"
        self.stdout.write(self.style.SUCCESS(f"Versión «{version.nombre}» {estado}."))

        if resultado.importancias:
            self.stdout.write("\n  Variables de mayor peso:")
            for i in resultado.importancias[:5]:
                self.stdout.write(f'    {i["peso"]:5.1f}%  {i["variable"]}')
