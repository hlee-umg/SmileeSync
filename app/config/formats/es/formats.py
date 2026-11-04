"""Formato numérico de Guatemala.

Django no incluye una configuración regional para es-GT, por lo que recae en la
de España: coma decimal y punto de millar (1.750,00). En Guatemala la
convención es la inversa (1,750.00), de modo que un monto o una cantidad de
horas se leían mal en pantalla. Solo se redefinen los separadores numéricos; el
resto de los formatos (fechas, horas) se toma de la configuración regional de
español que trae Django.
"""

DECIMAL_SEPARATOR = "."
THOUSAND_SEPARATOR = ","
NUMBER_GROUPING = 3
