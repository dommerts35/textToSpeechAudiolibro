import os
import sys
import logging
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from pdf_processor import PDFProcessor
from audio_manager import AudioManager
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_audiobook.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
console = Console()


class PDFToAudiobookConverter:
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.config.setup_directories()
        self.pdf_processor = PDFProcessor(self.config)
        self.audio_manager = AudioManager(self.config)

    def convert(self, pdf_path: str, output_path: str = None) -> bool:
        try:
            start_time = datetime.now()

            if not os.path.exists(pdf_path):
                console.print(f"❌ [red]Error: El archivo {pdf_path} no existe[/red]")
                return False

            if not output_path:
                base_name = os.path.splitext(os.path.basename(pdf_path))[0]
                output_dir = self.config.output_dir
                output_path = os.path.join(output_dir, f"{base_name}_audiobook.mp3")

            console.print(Panel.fit(
                f"[bold blue]CONVERSOR PROFESIONAL PDF A AUDIOLIBRO[/bold blue]\n"
                f"📁 Entrada: [cyan]{pdf_path}[/cyan]\n"
                f"🎵 Salida: [cyan]{output_path}[/cyan]",
                border_style="blue"
            ))

            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
            ) as progress:

                task1 = progress.add_task("[cyan]Extrayendo texto del PDF...", total=1)
                metadata = self.pdf_processor.extract_text_with_metadata(pdf_path)
                progress.update(task1, advance=1)

                self._show_document_info(metadata)

                task2 = progress.add_task("[green]Organizando en capítulos...", total=1)
                chapters = self.pdf_processor.split_into_chapters(metadata['text'])
                progress.update(task2, advance=1)

                task3 = progress.add_task("[yellow]Convirtiendo a audio...", total=len(chapters))

                conversion_results = self.audio_manager.convert_chapters_to_audio(
                    chapters,
                    output_path
                )

                for _ in chapters:
                    progress.update(task3, advance=1)

            self._show_conversion_results(conversion_results, start_time)
            return len(conversion_results['successful']) > 0

        except Exception as e:
            logger.error(f"Error en la conversión: {e}")
            console.print(f"❌ [red]Error durante la conversión: {e}[/red]")
            return False

    def _show_document_info(self, metadata: dict):

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Propiedad", style="cyan")
        table.add_column("Valor", style="white")

        table.add_row("Título", metadata['title'])
        table.add_row("Autor", metadata['author'])
        table.add_row("Páginas", str(metadata['pages']))
        table.add_row("Caracteres", f"{metadata['characters']:,}")
        table.add_row("Palabras", f"{metadata['words']:,}")

        console.print(Panel.fit(table, title="📊 [bold]INFORMACIÓN DEL DOCUMENTO[/bold]"))

    def _show_conversion_results(self, results: dict, start_time: datetime):
        duration = datetime.now() - start_time

        console.print(Panel.fit(
            f"[bold green]CONVERSIÓN COMPLETADA[/bold green]\n"
            f"⏱️  Duración: [cyan]{duration}[/cyan]\n"
            f"📑 Capítulos totales: [cyan]{results['total_chapters']}[/cyan]\n"
            f"✅ Exitosos: [green]{len(results['successful'])}[/green]\n"
            f"❌ Fallidos: [red]{len(results['failed'])}[/red]",
            border_style="green" if len(results['failed']) == 0 else "yellow"
        ))

        if results['successful']:
            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Capítulo", style="cyan")
            table.add_column("Archivo", style="white")
            table.add_column("Duración est.", style="green")
            table.add_column("Palabras", style="yellow")

            for chapter in results['successful']:
                filename = os.path.basename(chapter['file_path'])
                table.add_row(
                    chapter['title'][:30] + "..." if len(chapter['title']) > 30 else chapter['title'],
                    filename,
                    f"{chapter['duration_estimate']:.1f} min",
                    f"{chapter['words']:,}"
                )

            console.print(Panel.fit(table, title="🎵 [bold]ARCHIVOS DE AUDIO GENERADOS[/bold]"))

        if results['failed']:
            console.print(Panel.fit(
                f"[bold red]CAPÍTULOS CON ERRORES[/bold red]\n" +
                "\n".join([f"• {chap['index']}: {chap['title']}" for chap in results['failed']]),
                border_style="red"
            ))


def main():
    console.print("\n")
    console.print(Panel.fit(
        "[bold yellow]📚 CONVERSOR PROFESIONAL PDF A AUDIOLIBRO[/bold yellow]\n"
        "Convierte tus documentos PDF en audiolibros de alta calidad",
        border_style="yellow"
    ))

    if len(sys.argv) < 2:
        console.print("[cyan]Uso:[/cyan] python main.py <archivo_pdf> [archivo_salida]")
        console.print("[cyan]Ejemplo:[/cyan] python main.py mi_libro.pdf")
        console.print("\n[bold]O ingresa la ruta manualmente:[/bold]")

        pdf_path = input("📁 Ruta del PDF: ").strip().strip('"')
        if not pdf_path:
            console.print("❌ [red]Se requiere un archivo PDF[/red]")
            return
    else:
        pdf_path = sys.argv[1]

    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    converter = PDFToAudiobookConverter()
    success = converter.convert(pdf_path, output_path)

    if success:
        console.print(Panel.fit(
            "[bold green]🎊 PROCESO COMPLETADO EXITOSAMENTE[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold red]💥 ERROR EN EL PROCESO[/bold red]",
            border_style="red"
        ))


if __name__ == "__main__":

    main()

