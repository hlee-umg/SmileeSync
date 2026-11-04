from datetime import datetime, time, timedelta

from django import forms
from django.utils import timezone

from catalogo.models import Odontologo, Procedimiento
from pacientes.models import Paciente
from .disponibilidad import (
    asignar_unidad,
    franjas_efectivas,
    hay_traslape,
    unidades_activas,
)
from .models import AusenciaOdontologo, Cita, HorarioDisponibilidad

BASE = "form-control"
DIAS = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"]


def sumar_minutos(hora, minutos):
    """Suma minutos a un objeto time y devuelve el time resultante."""
    base = datetime.combine(datetime.today(), hora)
    return (base + timedelta(minutes=minutos)).time()


class CitaForm(forms.ModelForm):
    """Alta y reprogramación de citas.

    Valida que la cita quepa dentro de la disponibilidad declarada del
    odontólogo y que no se traslape con otra cita suya.
    """

    num_piezas = forms.IntegerField(
        label="Número de piezas",
        min_value=1,
        max_value=32,
        initial=1,
        help_text="Variable que utiliza el modelo predictivo para estimar la duración.",
        widget=forms.NumberInput(attrs={"class": BASE}),
    )

    class Meta:
        model = Cita
        fields = [
            "paciente",
            "odontologo",
            "procedimiento",
            "fecha",
            "hora_inicio_programada",
            "duracion_asignada_min",
            "observaciones",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": BASE}),
            "hora_inicio_programada": forms.TimeInput(
                attrs={"type": "time", "class": BASE}
            ),
            "duracion_asignada_min": forms.NumberInput(
                attrs={"class": BASE, "min": 10, "step": 5}
            ),
            "observaciones": forms.Textarea(attrs={"class": BASE, "rows": 2}),
        }
        labels = {
            "hora_inicio_programada": "Hora de inicio",
            "duracion_asignada_min": "Duración asignada (minutos)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["paciente"].queryset = Paciente.objects.filter(estado=True)
        self.fields["odontologo"].queryset = Odontologo.objects.filter(estado=True)
        self.fields["procedimiento"].queryset = Procedimiento.objects.filter(
            estado=True
        )
        for campo in self.fields.values():
            css = campo.widget.attrs.get("class", "")
            if not isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = (css + " " + BASE).strip()

    # ---------------------------------------------------------------- validación
    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        # Al reprogramar una cita antigua no se bloquea; solo al crear una nueva.
        if self.instance.pk is None and fecha < timezone.localdate():
            raise forms.ValidationError(
                "No se puede programar una cita en una fecha pasada."
            )
        return fecha

    def clean(self):
        limpio = super().clean()
        odontologo = limpio.get("odontologo")
        fecha = limpio.get("fecha")
        inicio = limpio.get("hora_inicio_programada")
        duracion = limpio.get("duracion_asignada_min")

        if not all([odontologo, fecha, inicio, duracion]):
            return limpio

        fin = sumar_minutos(inicio, duracion)
        if fin <= inicio:
            self.add_error(
                "duracion_asignada_min",
                "La duración debe hacer que la cita termine después de haber empezado.",
            )
            return limpio
        limpio["hora_fin_programada"] = fin

        # --- la cita debe caber en la disponibilidad efectiva del odontólogo ---
        # (patrón semanal menos las ausencias registradas para esa fecha)
        dia = DIAS[fecha.weekday()]
        tiene_patron = HorarioDisponibilidad.objects.filter(
            odontologo=odontologo, dia_semana=dia, estado=True
        ).exists()
        franjas = franjas_efectivas(odontologo, fecha)

        if not tiene_patron:
            self.add_error(
                "fecha",
                f"{odontologo} no tiene horario de atención configurado para "
                f"ese día de la semana.",
            )
        elif not franjas:
            self.add_error(
                "fecha",
                f"{odontologo} tiene registrada una ausencia que cubre toda "
                f'su jornada del {fecha.strftime("%d/%m/%Y")}.',
            )
        elif not any(f_ini <= inicio and fin <= f_fin for f_ini, f_fin in franjas):
            disponibles = ", ".join(
                f'{f_ini.strftime("%H:%M")} a {f_fin.strftime("%H:%M")}'
                for f_ini, f_fin in franjas
            )
            self.add_error(
                "hora_inicio_programada",
                f"La cita queda fuera del horario de atención. "
                f"{odontologo} atiende ese día de {disponibles}.",
            )

        # --- no puede traslaparse con otra cita del mismo odontólogo ---
        otras = Cita.objects.filter(
            odontologo=odontologo, fecha=fecha, estado=True
        ).exclude(estado_cita="CANCELADA")
        if self.instance.pk:
            otras = otras.exclude(pk=self.instance.pk)

        for otra in otras:
            if hay_traslape(
                inicio, fin, otra.hora_inicio_programada, otra.hora_fin_programada
            ):
                self.add_error(
                    "hora_inicio_programada",
                    f"Se traslapa con la cita de {otra.paciente} "
                    f'({otra.hora_inicio_programada.strftime("%H:%M")} a '
                    f'{otra.hora_fin_programada.strftime("%H:%M")}).',
                )
                break

        # --- debe quedar una unidad dental libre ---
        # Es la restricción física de la clínica: hay menos sillones que
        # odontólogos, de modo que dos profesionales libres a la misma hora no
        # significan dos citas simultáneas posibles.
        unidades = unidades_activas()
        if not unidades:
            self.add_error(
                None,
                "No hay unidades dentales activas en el catálogo, por lo "
                "que no es posible programar citas.",
            )
        else:
            libre = asignar_unidad(fecha, inicio, fin, excluir_cita=self.instance.pk)
            if libre is None:
                cuantas = (
                    "La única unidad dental está ocupada"
                    if len(unidades) == 1
                    else f"Las {len(unidades)} unidades dentales están ocupadas"
                )
                self.add_error(
                    "hora_inicio_programada",
                    f"{cuantas} en ese horario. Elija otro espacio o consulte la "
                    f"recomendación del calendario.",
                )
            else:
                limpio["unidad"] = libre

        return limpio

    def save(self, commit=True):
        cita = super().save(commit=False)
        cita.hora_fin_programada = sumar_minutos(
            cita.hora_inicio_programada, cita.duracion_asignada_min
        )
        # La unidad se asigna sola: son intercambiables, así que se toma la
        # primera libre en lugar de pedírsela al usuario.
        if self.cleaned_data.get("unidad"):
            cita.unidad = self.cleaned_data["unidad"]
        if commit:
            cita.save()
        return cita


class HorarioForm(forms.ModelForm):
    """Alta de una franja de disponibilidad de un odontólogo.

    Sin franjas configuradas el sistema rechaza todas sus citas, por lo que
    esta pantalla es requisito para que un odontólogo nuevo pueda atender.
    """

    replicar = forms.BooleanField(
        label="Aplicar esta franja de lunes a viernes",
        required=False,
        help_text="Evita repetir la misma franja día por día.",
        widget=forms.CheckboxInput(),
    )

    class Meta:
        model = HorarioDisponibilidad
        fields = ["dia_semana", "hora_inicio", "hora_fin"]
        widgets = {
            "hora_inicio": forms.TimeInput(attrs={"type": "time", "class": BASE}),
            "hora_fin": forms.TimeInput(attrs={"type": "time", "class": BASE}),
        }
        labels = {"dia_semana": "Día de la semana"}

    def __init__(self, *args, odontologo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.odontologo = odontologo
        self.fields["dia_semana"].widget.attrs["class"] = "form-select"

    def clean(self):
        limpio = super().clean()
        dia = limpio.get("dia_semana")
        inicio = limpio.get("hora_inicio")
        fin = limpio.get("hora_fin")

        if not (dia and inicio and fin):
            return limpio

        if fin <= inicio:
            self.add_error(
                "hora_fin", "La hora de finalización debe ser posterior a la de inicio."
            )
            return limpio

        # Los días a verificar: solo el elegido, o los cinco días hábiles.
        dias = DIAS[:5] if limpio.get("replicar") else [dia]

        for d in dias:
            existentes = HorarioDisponibilidad.objects.filter(
                odontologo=self.odontologo, dia_semana=d, estado=True
            )
            if self.instance.pk:
                existentes = existentes.exclude(pk=self.instance.pk)
            for franja in existentes:
                if hay_traslape(inicio, fin, franja.hora_inicio, franja.hora_fin):
                    etiqueta = dict(HorarioDisponibilidad.DIAS).get(d, d)
                    self.add_error(
                        "hora_inicio",
                        f"La franja se traslapa con una ya registrada el {etiqueta} "
                        f'({franja.hora_inicio.strftime("%H:%M")} a '
                        f'{franja.hora_fin.strftime("%H:%M")}).',
                    )
                    return limpio
        return limpio

    def guardar(self):
        """Crea la franja en el día elegido, o en los cinco días hábiles."""
        datos = self.cleaned_data
        dias = DIAS[:5] if datos.get("replicar") else [datos["dia_semana"]]
        creadas = []
        for d in dias:
            franja, creada = HorarioDisponibilidad.objects.get_or_create(
                odontologo=self.odontologo,
                dia_semana=d,
                hora_inicio=datos["hora_inicio"],
                defaults={"hora_fin": datos["hora_fin"], "estado": True},
            )
            if not creada and not franja.estado:
                franja.estado = True
                franja.hora_fin = datos["hora_fin"]
                franja.save(update_fields=["estado", "hora_fin"])
                creada = True
            if creada:
                creadas.append(franja)
        return creadas


class RegistrarTiemposForm(forms.ModelForm):
    """Registro de los tiempos reales al finalizar la atención.

    Es el dato del que depende el aprendizaje del modelo predictivo.
    """

    class Meta:
        model = Cita
        fields = ["hora_inicio_real", "hora_fin_real"]
        widgets = {
            "hora_inicio_real": forms.TimeInput(attrs={"type": "time", "class": BASE}),
            "hora_fin_real": forms.TimeInput(attrs={"type": "time", "class": BASE}),
        }
        labels = {
            "hora_inicio_real": "Hora real de inicio",
            "hora_fin_real": "Hora real de finalización",
        }

    def clean(self):
        limpio = super().clean()
        inicio = limpio.get("hora_inicio_real")
        fin = limpio.get("hora_fin_real")
        if inicio and fin:
            if fin <= inicio:
                self.add_error(
                    "hora_fin_real",
                    "La hora de finalización debe ser posterior a la de inicio.",
                )
            else:
                minutos = (
                    datetime.combine(datetime.today(), fin)
                    - datetime.combine(datetime.today(), inicio)
                ).seconds // 60
                limpio["duracion_real_min"] = minutos
        return limpio

    def save(self, commit=True):
        cita = super().save(commit=False)
        if self.cleaned_data.get("duracion_real_min"):
            cita.duracion_real_min = self.cleaned_data["duracion_real_min"]
        cita.estado_cita = "ATENDIDA"
        if commit:
            cita.save()
        return cita


class AusenciaForm(forms.ModelForm):
    """Registro de una ausencia puntual del odontólogo.

    Es la excepción al patrón semanal: el horario habitual sigue vigente y esta
    fecha concreta queda descontada de su disponibilidad.
    """

    class Meta:
        model = AusenciaOdontologo
        fields = ["fecha", "todo_el_dia", "hora_inicio", "hora_fin", "motivo"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": BASE}),
            "hora_inicio": forms.TimeInput(attrs={"type": "time", "class": BASE}),
            "hora_fin": forms.TimeInput(attrs={"type": "time", "class": BASE}),
            "motivo": forms.TextInput(
                attrs={"class": BASE, "placeholder": "Congreso, vacaciones…"}
            ),
        }
        labels = {"todo_el_dia": "Toda la jornada"}

    def __init__(self, *args, odontologo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.odontologo = odontologo
        self.fields["todo_el_dia"].initial = True
        for campo in ("hora_inicio", "hora_fin", "motivo"):
            self.fields[campo].required = False

    def clean(self):
        limpio = super().clean()
        if limpio.get("todo_el_dia"):
            # Se guarda la jornada completa para que el cálculo de
            # disponibilidad tenga siempre un intervalo con el que operar.
            limpio["hora_inicio"] = time(0, 0)
            limpio["hora_fin"] = time(23, 59)
            return limpio

        inicio, fin = limpio.get("hora_inicio"), limpio.get("hora_fin")
        if not inicio or not fin:
            self.add_error(
                "hora_inicio", "Indique el rango de horas, o marque toda la jornada."
            )
        elif fin <= inicio:
            self.add_error(
                "hora_fin", "La hora de finalización debe ser posterior a la de inicio."
            )
        return limpio

    def save(self, commit=True):
        ausencia = super().save(commit=False)
        ausencia.odontologo = self.odontologo
        ausencia.hora_inicio = self.cleaned_data["hora_inicio"]
        ausencia.hora_fin = self.cleaned_data["hora_fin"]
        if commit:
            ausencia.save()
        return ausencia
