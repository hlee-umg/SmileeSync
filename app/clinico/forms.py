"""Formularios del expediente clínico."""

from datetime import time
from decimal import Decimal

from django import forms
from django.utils import timezone

from catalogo.models import Odontologo, Procedimiento

from .models import DetallePlan, Hallazgo, NotaClinica, Pago, PlanTratamiento
from .piezas import es_valida

BASE = "form-control"


def _estilizar(campos):
    for campo in campos.values():
        css = campo.widget.attrs.get("class", "")
        if isinstance(campo.widget, (forms.Select, forms.SelectMultiple)):
            campo.widget.attrs["class"] = (css + " form-select").strip()
        elif not isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs["class"] = (css + " " + BASE).strip()


class HallazgoForm(forms.ModelForm):
    """Registro de un hallazgo en el odontograma.

    La pieza llega desde la arcada dibujada en la pantalla, por lo que se valida
    contra la nomenclatura FDI en lugar de confiar en el `select`.
    """

    class Meta:
        model = Hallazgo
        fields = ["pieza", "cara", "tipo", "fecha", "observacion"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.TextInput(
                attrs={"placeholder": "Detalle opcional del hallazgo"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["observacion"].required = False
        self.fields["fecha"].initial = timezone.localdate()
        _estilizar(self.fields)

    def clean_pieza(self):
        pieza = self.cleaned_data.get("pieza")
        if not es_valida(pieza):
            raise forms.ValidationError(
                "La pieza indicada no existe en la "
                "nomenclatura FDI de dentición permanente."
            )
        return pieza

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError("No se puede fechar un hallazgo en el futuro.")
        return fecha

    def clean(self):
        limpio = super().clean()
        tipo, cara = limpio.get("tipo"), limpio.get("cara")
        # Una pieza ausente o indicada para extracción es una condición de toda
        # la pieza: registrarla en una sola cara daría un odontograma
        # contradictorio (una cara ausente y las demás presentes).
        if tipo in ("AUSENTE", "EXTRACCION", "IMPLANTE") and cara != "TODA":
            self.add_error(
                "cara",
                f"«{dict(Hallazgo.TIPOS)[tipo]}» describe la pieza "
                f"completa, no una cara.",
            )
        return limpio


class NotaClinicaForm(forms.ModelForm):
    """Nota de evolución de una visita.

    Los campos de piezas, anestesia y complicación no son documentación
    decorativa: son las variables que el modelo predictivo necesita para
    explicar por qué dos citas del mismo procedimiento duran distinto.
    """

    class Meta:
        model = NotaClinica
        fields = [
            "odontologo",
            "fecha",
            "motivo",
            "hallazgos_clinicos",
            "procedimiento_realizado",
            "piezas_tratadas",
            "num_piezas",
            "anestesia",
            "materiales",
            "complicacion",
            "detalle_complicacion",
            "indicaciones",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "hallazgos_clinicos": forms.Textarea(attrs={"rows": 3}),
            "procedimiento_realizado": forms.Textarea(attrs={"rows": 3}),
            "indicaciones": forms.Textarea(attrs={"rows": 2}),
            "num_piezas": forms.NumberInput(attrs={"min": 0, "max": 32}),
            "piezas_tratadas": forms.TextInput(attrs={"placeholder": "16, 26"}),
            "detalle_complicacion": forms.TextInput(
                attrs={"placeholder": "Solo si hubo complicación"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["odontologo"].queryset = Odontologo.objects.filter(estado=True)
        for campo in (
            "hallazgos_clinicos",
            "piezas_tratadas",
            "materiales",
            "detalle_complicacion",
            "indicaciones",
        ):
            self.fields[campo].required = False
        self.fields["fecha"].initial = timezone.localdate()
        _estilizar(self.fields)

    def clean_piezas_tratadas(self):
        texto = (self.cleaned_data.get("piezas_tratadas") or "").strip()
        if not texto:
            return ""
        piezas = [p.strip() for p in texto.split(",") if p.strip()]
        invalidas = [p for p in piezas if not es_valida(p)]
        if invalidas:
            raise forms.ValidationError(
                f'No corresponden a piezas FDI válidas: {", ".join(invalidas)}.'
            )
        return ", ".join(piezas)

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError("No se puede fechar una nota en el futuro.")
        return fecha

    def clean(self):
        limpio = super().clean()
        piezas = [
            p for p in (limpio.get("piezas_tratadas") or "").split(",") if p.strip()
        ]
        # El número de piezas es la variable que entra al modelo; si se enumeran
        # las piezas, debe coincidir con ellas para que el dato no se contradiga.
        if piezas and limpio.get("num_piezas") not in (None, len(piezas)):
            self.add_error(
                "num_piezas",
                f"Se enumeraron {len(piezas)} pieza"
                f'{"s" if len(piezas) != 1 else ""}; el número debe '
                f"coincidir.",
            )
        if (
            limpio.get("complicacion")
            and not (limpio.get("detalle_complicacion") or "").strip()
        ):
            self.add_error(
                "detalle_complicacion",
                "Describa la complicación: es el dato que explica una "
                "duración fuera de lo previsto.",
            )
        return limpio


class PlanTratamientoForm(forms.ModelForm):
    class Meta:
        model = PlanTratamiento
        fields = ["odontologo", "fecha", "diagnostico", "descuento", "observaciones"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "diagnostico": forms.Textarea(attrs={"rows": 3}),
            "observaciones": forms.Textarea(attrs={"rows": 2}),
            "descuento": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
        }
        labels = {"odontologo": "Odontólogo responsable"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["odontologo"].queryset = Odontologo.objects.filter(estado=True)
        self.fields["observaciones"].required = False
        self.fields["descuento"].required = False
        self.fields["fecha"].initial = timezone.localdate()
        _estilizar(self.fields)

    def clean_descuento(self):
        descuento = self.cleaned_data.get("descuento")
        if descuento is None:
            return Decimal("0.00")
        if descuento < 0:
            raise forms.ValidationError("El descuento no puede ser negativo.")
        return descuento

    def clean_diagnostico(self):
        texto = (self.cleaned_data.get("diagnostico") or "").strip()
        if len(texto) < 10:
            raise forms.ValidationError(
                "Describa el diagnóstico que justifica el plan."
            )
        return texto


class DetallePlanForm(forms.ModelForm):
    """Renglón del plan.

    El precio y la duración se precargan del catálogo y del servicio de
    estimación, pero quedan editables: el presupuesto es un acuerdo con el
    paciente, no un cálculo cerrado.
    """

    class Meta:
        model = DetallePlan
        fields = ["fase", "procedimiento", "pieza", "num_piezas", "precio_unitario"]
        widgets = {
            "fase": forms.NumberInput(attrs={"min": 1, "max": 20}),
            "num_piezas": forms.NumberInput(attrs={"min": 1, "max": 32}),
            "precio_unitario": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
        }
        labels = {"pieza": "Pieza (opcional)", "precio_unitario": "Precio unitario (Q)"}

    def __init__(self, *args, plan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = plan
        self.fields["procedimiento"].queryset = Procedimiento.objects.filter(
            estado=True
        )
        self.fields["pieza"].required = False
        self.fields["precio_unitario"].required = False
        # El campo del modelo tiene 0.00 por omisión, de modo que el formulario
        # lo mostraría precargado en cero y un renglón guardado sin tocarlo
        # quedaría gratis. Se deja en blanco: vacío significa «usar la tarifa
        # del catálogo», que es lo que dice la ayuda.
        self.initial["precio_unitario"] = None
        _estilizar(self.fields)

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get("precio_unitario")
        if precio is None:
            return None  # se resuelve en clean() con el precio del catálogo
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio

    def clean(self):
        limpio = super().clean()
        procedimiento = limpio.get("procedimiento")
        if procedimiento and limpio.get("precio_unitario") is None:
            limpio["precio_unitario"] = procedimiento.precio or Decimal("0.00")
        return limpio

    def save(self, commit=True):
        """Guarda el renglón estimando su duración con el modelo predictivo.

        La estimación se resuelve aquí, y no en la vista, porque es parte de lo
        que define al renglón: el plan presupuesta tiempo igual que presupuesta
        dinero.
        """
        from inteligencia.servicio import estimar_duracion

        detalle = super().save(commit=False)
        detalle.plan = self.plan
        if detalle.precio_unitario is None:
            detalle.precio_unitario = detalle.procedimiento.precio or Decimal("0.00")

        estimacion = estimar_duracion(
            detalle.procedimiento,
            self.plan.odontologo,
            self.plan.fecha,
            time(9, 0),
            detalle.num_piezas,
        )
        detalle.duracion_estimada_min = estimacion.duracion_min
        detalle.origen_estimacion = estimacion.origen

        # El orden dentro de la fase se asigna solo: el usuario ya indicó la
        # fase y no tiene por qué llevar la cuenta de los renglones.
        ultimo = (
            DetallePlan.objects.filter(plan=self.plan, fase=detalle.fase)
            .order_by("-orden")
            .first()
        )
        detalle.orden = (ultimo.orden + 1) if ultimo else 1

        if commit:
            detalle.save()
        return detalle


class PagoForm(forms.ModelForm):
    """Abono aplicado a un plan. No admite cobrar más que el saldo vigente."""

    class Meta:
        model = Pago
        fields = ["fecha", "monto", "metodo", "referencia", "observaciones"]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "monto": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "referencia": forms.TextInput(
                attrs={"placeholder": "N.° de recibo o boleta"}
            ),
        }

    def __init__(self, *args, plan=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.plan = plan
        self.fields["fecha"].initial = timezone.localdate()
        for campo in ("referencia", "observaciones"):
            self.fields[campo].required = False
        _estilizar(self.fields)

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if monto is None:
            return monto
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor que cero.")
        if self.plan and monto > self.plan.saldo:
            raise forms.ValidationError(
                f"El abono excede el saldo pendiente (Q{self.plan.saldo:.2f})."
            )
        return monto

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError(
                "No se puede registrar un abono con fecha futura."
            )
        return fecha

    def save(self, commit=True):
        pago = super().save(commit=False)
        pago.plan = self.plan
        if commit:
            pago.save()
        return pago
