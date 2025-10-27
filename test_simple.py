import PyPDF2
from gtts import gTTS
import os


def convert_pdf_simple(pdf_path, output_path):
    try:
        print(f"📖 Leyendo PDF: {pdf_path}")

        if not os.path.exists(pdf_path):
            print(f"❌ Error: El archivo {pdf_path} no existe")
            return False

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""

            print(f"📄 Número de páginas: {len(pdf_reader.pages)}")

            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += page_text + "\n"
                print(f"✅ Página {page_num + 1} procesada")

        print(f"📝 Texto extraído: {len(text)} caracteres")

        if text.strip():

            print("--- PRIMEROS 500 CARACTERES ---")
            print(text[:500])
            print("--- FIN DEL PREVIEW ---")

            test_text = text[:2000] if len(text) > 2000 else text
            print(f"🎙️ Convirtiendo {len(test_text)} caracteres a audio...")

            tts = gTTS(text=test_text, lang='es', slow=False)
            tts.save(output_path)

            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ Audio guardado en: {output_path}")
                print(f"📊 Tamaño del archivo: {file_size} bytes")
                return True
            else:
                print("❌ Error: No se pudo crear el archivo de audio")
                return False
        else:
            print("❌ Error: No se pudo extraer texto del PDF")
            print("💡 Posibles causas:")
            print("   - El PDF está escaneado (solo imágenes)")
            print("   - El PDF está protegido")
            print("   - El PDF está vacío")
            return False

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


if __name__ == "__main__":

    pdf_file = "test.pdf"

    if not os.path.exists(pdf_file):
        print("⚠️  Archivo 'test.pdf' no encontrado")
        pdf_file = input("📝 Ingresa la ruta de tu archivo PDF: ").strip().strip('"')

    output_file = "audio_salida.mp3"

    print("🚀 INICIANDO CONVERSIÓN DE PDF A AUDIO...")
    success = convert_pdf_simple(pdf_file, output_file)

    if success:
        print("\n🎉 ¡CONVERSIÓN EXITOSA!")
        print(f"🔊 El archivo de audio está en: {os.path.abspath(output_file)}")
    else:

        print("\n💥 CONVERSIÓN FALLIDA")
