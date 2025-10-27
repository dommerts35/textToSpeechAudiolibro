import streamlit as st
import os
import sys
from pathlib import Path
import tempfile
import base64

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdf_processor import PDFProcessor
from audio_manager import AudioManager
from config import Config

st.set_page_config(
    page_title="PDF to Audiobook Converter",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .chapter-card {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)


class StreamlitApp:
    def __init__(self):
        self.config = Config()
        self.pdf_processor = PDFProcessor(self.config)
        self.audio_manager = AudioManager(self.config)

    def run(self):
        st.markdown('<h1 class="main-header">📚 PDF to Audiobook Converter</h1>', unsafe_allow_html=True)

        with st.sidebar:
            st.header("⚙️ Configuración")

            st.subheader("Configuración de Audio")
            language = st.selectbox(
                "Idioma de la voz",
                ["es", "en", "fr", "de", "it", "pt"],
                index=0,
                help="Selecciona el idioma para la conversión de texto a voz"
            )

            slow_speech = st.checkbox(
                "Voz lenta",
                value=False,
                help="Habilita para una voz más lenta y clara"
            )

            st.subheader("Procesamiento")
            detect_chapters = st.checkbox(
                "Detección automática de capítulos",
                value=True,
                help="Intenta detectar y separar capítulos automáticamente"
            )

            max_chunk_size = st.slider(
                "Tamaño máximo de chunk (caracteres)",
                min_value=1000,
                max_value=5000,
                value=4000,
                step=500,
                help="Tamaño máximo de texto por archivo de audio"
            )

            self.config.tts.language = language
            self.config.tts.slow = slow_speech
            self.config.tts.max_chunk_length = max_chunk_size

        col1, col2 = st.columns([2, 1])

        with col1:
            st.header("📤 Subir PDF")

            uploaded_file = st.file_uploader(
                "Selecciona un archivo PDF",
                type="pdf",
                help="Sube el archivo PDF que quieres convertir a audiolibro"
            )

            if uploaded_file is not None:

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    pdf_path = tmp_file.name


                file_size = uploaded_file.size / (1024 * 1024)
                st.info(f"📄 **Archivo:** {uploaded_file.name} | 📊 **Tamaño:** {file_size:.2f} MB")

                if st.button("🎧 Convertir a Audiobook", type="primary", use_container_width=True):
                    self.process_pdf(pdf_path, uploaded_file.name)

                if os.path.exists(pdf_path):
                    os.unlink(pdf_path)

        with col2:
            st.header("ℹ️ Información")
            st.markdown("""
            <div class="info-box">
            <h4>✨ Características:</h4>
            <ul>
            <li>Conversión de PDF a audio MP3</li>
            <li>Detección automática de capítulos</li>
            <li>Múltiples idiomas soportados</li>
            <li>Procesamiento de textos largos</li>
            <li>Interfaz fácil de usar</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="info-box">
            <h4>📋 Formatos soportados:</h4>
            <ul>
            <li>PDF con texto seleccionable</li>
            <li>Máximo: 50 MB por archivo</li>
            <li>Idiomas: ES, EN, FR, DE, IT, PT</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

    def process_pdf(self, pdf_path: str, original_filename: str):
        """Procesa el PDF y convierte a audio"""
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()


            status_text.text("📖 Extrayendo texto del PDF...")
            metadata = self.pdf_processor.extract_text_with_metadata(pdf_path)
            progress_bar.progress(25)

            with st.expander("📊 Información del Documento", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Título",
                              metadata['title'][:30] + "..." if len(metadata['title']) > 30 else metadata['title'])
                with col2:
                    st.metric("Páginas", metadata['pages'])
                with col3:
                    st.metric("Palabras", f"{metadata['words']:,}")

            status_text.text("📑 Organizando en capítulos...")
            chapters = self.pdf_processor.split_into_chapters(metadata['text'])
            progress_bar.progress(50)

            if len(chapters) > 1:
                with st.expander(f"📖 Capítulos Detectados ({len(chapters)})", expanded=True):
                    for i, chapter in enumerate(chapters):
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{i + 1}. {chapter['title']}**")
                                st.caption(
                                    f"{chapter.get('words', 0)} palabras | ~{chapter.get('duration_estimate', 0):.1f} min")
                            with col2:
                                st.text(f"Capítulo {i + 1}")

            status_text.text("🎙️ Convirtiendo a audio...")

            output_dir = "streamlit_outputs"
            os.makedirs(output_dir, exist_ok=True)

            base_name = Path(original_filename).stem
            output_path = os.path.join(output_dir, f"{base_name}_audiobook.mp3")

            results = self.audio_manager.convert_chapters_to_audio(chapters, output_path)
            progress_bar.progress(100)

            self.show_results(results, output_dir)

            status_text.text("✅ Conversión completada!")

        except Exception as e:
            st.error(f"❌ Error durante la conversión: {str(e)}")

    def show_results(self, results: dict, output_dir: str):
        """Muestra los resultados de la conversión"""
        st.header("🎉 Conversión Completada")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Capítulos Totales", results['total_chapters'])
        with col2:
            st.metric("Conversiones Exitosas", len(results['successful']))
        with col3:
            st.metric("Errores", len(results['failed']))

        if results['successful']:
            st.subheader("📁 Archivos de Audio Generados")

            for chapter in results['successful']:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.markdown(f"**{chapter['title']}**")

                    with col2:
                        st.text(f"{chapter['duration_estimate']:.1f} min")

                    with col3:
                        with open(chapter['file_path'], "rb") as file:
                            btn = st.download_button(
                                label="📥 Descargar",
                                data=file,
                                file_name=os.path.basename(chapter['file_path']),
                                mime="audio/mpeg",
                                key=f"dl_{chapter['file_path']}"
                            )

            if len(results['successful']) > 1:
                st.info("💡 Para descargar todos los archivos, haz clic en cada botón de descarga individualmente.")

        if results['failed']:
            st.warning(f"⚠️ {len(results['failed'])} capítulos tuvieron errores en la conversión.")


def main():
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":

    main()
