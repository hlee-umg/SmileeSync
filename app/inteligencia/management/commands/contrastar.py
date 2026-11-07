"""Contrasta la hipótesis de trabajo sobre el conjunto vigente."""

from django.core.management.base import BaseCommand

from inteligencia.contraste import contrastar


class Command(BaseCommand):
    help = "Contrasta H0 con la prueba de rangos con signo de Wilcoxon."

    def handle(self, *args, **opciones):
        r = contrastar()
        if r is None:
            self.stdout.write(self.style.ERROR("No hay registros suficientes."))
            return
        self.stdout.write(f"Atenciones contrastadas: {r['n']}")
        self.stdout.write(f"  MAE del catálogo:  {r['mae_catalogo']} min")
        self.stdout.write(f"  MAE del modelo:    {r['mae_modelo']} min")
        self.stdout.write(
            f"  Reducción:         {r['reduccion_pct']} %" f"  (meta {r['meta_pct']} %)"
        )
        self.stdout.write(f"  Pares no nulos:    {r['pares']}")
        self.stdout.write(f"  W+ = {r['w_mas']}   z = {r['z']}   p = {r['p']:.3e}")
        self.stdout.write(f"  Mediana de la diferencia: {r['mediana_diferencia']} min")
        veredicto = "Se rechaza H0" if r["rechaza_h0"] else "No se rechaza H0"
        self.stdout.write(self.style.SUCCESS(f"  {veredicto}"))
