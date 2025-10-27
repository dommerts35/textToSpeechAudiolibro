# crear_pdf_prueba.py
from reportlab.pdfgen import canvas
import os


def crear_pdf_prueba():
    """Crea un PDF simple de prueba"""
    filename = "test.pdf"

    c = canvas.Canvas(filename)

    # Configurar título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 800, "Libro de Prueba para Conversión")

    # Configurar autor
    c.setFont("Helvetica", 12)
    c.drawString(100, 770, "Por: Asistente de Python")

    # Texto de ejemplo
    texto = [
        "Este es un párrafo de ejemplo para probar la conversión",
        "de PDF a audiolibro. Contiene varias oraciones en español",
        "para verificar que el sistema de texto a voz funciona",
        "correctamente con caracteres especiales y acentos.",
        "",
        "El segundo párrafo continúa con más texto de prueba.",
        "Aquí podemos incluir números: 123, símbolos: ¡¿!?, y",
        "caracteres especiales del español como ñ, á, é, í, ó, ú.",
        "",
        "Finalmente, este es el tercer párrafo que demuestra",
        "que la conversión funciona con múltiples páginas y",
        "párrafos de diferentes longitudes."
    ]

    c.setFont("Helvetica", 10)
    y_position = 730

    for linea in texto:
        if y_position < 50:  # Nueva página si se acaba el espacio
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = 800

        c.drawString(50, y_position, linea)
        y_position -= 20

    c.save()
    print(f"✅ PDF de prueba creado: {filename}")


if __name__ == "__main__":
    crear_pdf_prueba()