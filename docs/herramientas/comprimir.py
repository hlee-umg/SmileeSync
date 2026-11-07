"""Reduce el peso de las imágenes del documento sin cambiar su presentación.

Las capturas se tomaron con factor de escala dos, de modo que llegan al
documento con el doble de resolución de la que la página necesita. El tamaño
con que se muestran está fijado en el XML, así que reducir los píxeles no altera
la maquetación ni la paginación.
"""
import io
import pathlib
import shutil
import zipfile

from PIL import Image

A = pathlib.Path.home() / 'mnt/Documents--UMG_Hee--proyecto de Graduacion 2/SmileeSync/docs/SmileeSync_Cuarta_Entrega.docx'
LADO_MAX = 2000


def main():
    respaldo = pathlib.Path.home() / 'tesis/respaldo_pre_comprimir.docx'
    shutil.copy(A, respaldo)

    origen = zipfile.ZipFile(respaldo)
    salida = io.BytesIO()
    ahorro = 0
    reducidas = 0
    with zipfile.ZipFile(salida, 'w', zipfile.ZIP_DEFLATED) as nuevo:
        for info in origen.infolist():
            datos = origen.read(info.filename)
            if info.filename.startswith('word/media/') and \
                    info.filename.lower().endswith('.png'):
                try:
                    with Image.open(io.BytesIO(datos)) as im:
                        im.load()
                        ancho, alto = im.size
                        escala = LADO_MAX / max(ancho, alto)
                        if escala < 1:
                            im = im.resize((round(ancho * escala),
                                            round(alto * escala)),
                                           Image.LANCZOS)
                        if im.mode not in ('RGB', 'RGBA', 'L', 'P'):
                            im = im.convert('RGB')
                        buf = io.BytesIO()
                        im.save(buf, format='PNG', optimize=True)
                    if buf.tell() < len(datos):
                        ahorro += len(datos) - buf.tell()
                        reducidas += 1
                        datos = buf.getvalue()
                except Exception as e:
                    print(f'   se conserva {info.filename}: {e}')
            nuevo.writestr(info, datos)
    origen.close()
    A.write_bytes(salida.getvalue())
    print(f'{reducidas} imágenes reducidas; {ahorro/1e6:.1f} MB menos en los medios')
    print(f'documento: {A.stat().st_size/1e6:.1f} MB')


if __name__ == '__main__':
    main()
