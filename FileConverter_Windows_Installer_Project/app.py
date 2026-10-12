"""Local desktop file converter: PDF <-> images, and image formats."""
from __future__ import annotations

import queue
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz  # PyMuPDF
from PIL import Image, ImageOps, UnidentifiedImageError

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.gif'}
PDF_EXTENSIONS = {'.pdf'}
TARGETS = ('JPG', 'PNG', 'WEBP', 'BMP', 'TIFF', 'PDF')


def safe_name(path: Path) -> str:
    return ''.join(ch if ch.isalnum() or ch in '-_.' else '_' for ch in path.stem).strip('._') or 'file'


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for i in range(2, 100000):
        candidate = path.with_name(f'{path.stem}_{i}{path.suffix}')
        if not candidate.exists():
            return candidate
    raise RuntimeError('Too many output files with the same name')


def rgb_image(image: Image.Image) -> Image.Image:
    image = ImageOps.exif_transpose(image)
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        rgba = image.convert('RGBA')
        background = Image.new('RGB', rgba.size, 'white')
        background.paste(rgba, mask=rgba.getchannel('A'))
        return background
    return image.convert('RGB')


def convert_file(source: Path, target: str, output_dir: Path, dpi: int = 150) -> list[Path]:
    """Convert one file. A multi-page PDF to images produces one image per page."""
    target = target.upper()
    ext = source.suffix.lower()
    if target not in TARGETS:
        raise ValueError('Unsupported output format')
    if ext not in IMAGE_EXTENSIONS | PDF_EXTENSIONS:
        raise ValueError(f'Unsupported input format: {ext}')
    output_dir.mkdir(parents=True, exist_ok=True)
    name = safe_name(source)
    results: list[Path] = []

    if ext == '.pdf':
        if target == 'PDF':
            raise ValueError('Choose an image format when converting a PDF')
        with fitz.open(source) as doc:
            if doc.needs_pass:
                raise ValueError('Password-protected PDFs are not supported')
            if doc.page_count == 0:
                raise ValueError('PDF has no pages')
            for index, page in enumerate(doc, 1):
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
                with Image.frombytes('RGB', (pix.width, pix.height), pix.samples) as img:
                    destination = unique_path(output_dir / f'{name}_page_{index:03d}.{target.lower()}')
                    save_image(img, destination, target)
                    results.append(destination)
        return results

    with Image.open(source) as opened:
        # First frame of animated/multipage image files; document this behavior.
        opened.seek(0)
        image = rgb_image(opened)
        destination = unique_path(output_dir / f'{name}.{target.lower()}')
        if target == 'PDF':
            image.save(destination, 'PDF', resolution=100.0)
        else:
            save_image(image, destination, target)
        results.append(destination)
        image.close()
    return results


def save_image(image: Image.Image, destination: Path, target: str) -> None:
    options = {'quality': 92} if target in ('JPG', 'WEBP') else {}
    fmt = 'JPEG' if target == 'JPG' else target
    image.save(destination, format=fmt, **options)


class ConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('File Converter — Offline')
        self.geometry('780x590')
        self.minsize(650, 480)
        self.files: list[Path] = []
        self.events: queue.Queue = queue.Queue()
        self.busy = False
        self.target = tk.StringVar(value='PNG')
        self.output_dir = tk.StringVar(value=str(Path.home() / 'Converted Files'))
        self.dpi = tk.IntVar(value=150)
        self.status = tk.StringVar(value='Add PDF or image files to begin.')
        self.progress = tk.DoubleVar(value=0)
        self.build_ui()
        self.after(100, self.poll_events)

    def build_ui(self):
        self.configure(bg='#f3f6fb')
        outer = ttk.Frame(self, padding=22)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='File Converter', font=('Arial', 23, 'bold')).pack(anchor='w')
        ttk.Label(outer, text='Convert PDFs and images locally. Your files never leave your computer.').pack(anchor='w', pady=(2, 16))

        toolbar = ttk.Frame(outer)
        toolbar.pack(fill='x', pady=(0, 8))
        self.add_btn = ttk.Button(toolbar, text='＋ Add files', command=self.add_files)
        self.add_btn.pack(side='left')
        self.remove_btn = ttk.Button(toolbar, text='Remove selected', command=self.remove_selected)
        self.remove_btn.pack(side='left', padx=8)
        self.clear_btn = ttk.Button(toolbar, text='Clear all', command=self.clear_files)
        self.clear_btn.pack(side='left')

        list_frame = ttk.Frame(outer)
        list_frame.pack(fill='both', expand=True)
        self.file_list = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=10, font=('Arial', 10))
        scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scroll.set)
        self.file_list.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

        settings = ttk.LabelFrame(outer, text='Conversion settings', padding=12)
        settings.pack(fill='x', pady=(14, 8))
        ttk.Label(settings, text='Convert to:').grid(row=0, column=0, sticky='w')
        self.format_combo = ttk.Combobox(settings, textvariable=self.target, values=TARGETS, state='readonly', width=12)
        self.format_combo.grid(row=0, column=1, sticky='w', padx=(8, 22))
        ttk.Label(settings, text='PDF rendering DPI:').grid(row=0, column=2, sticky='w')
        self.dpi_combo = ttk.Combobox(settings, textvariable=self.dpi, values=(72, 150, 200, 300), state='readonly', width=7)
        self.dpi_combo.grid(row=0, column=3, sticky='w', padx=8)
        ttk.Label(settings, text='Output folder:').grid(row=1, column=0, sticky='w', pady=(12, 0))
        ttk.Entry(settings, textvariable=self.output_dir).grid(row=1, column=1, columnspan=3, sticky='ew', padx=(8, 8), pady=(12, 0))
        self.browse_btn = ttk.Button(settings, text='Browse…', command=self.choose_folder)
        self.browse_btn.grid(row=1, column=4, pady=(12, 0))
        settings.columnconfigure(2, weight=1)

        self.convert_btn = ttk.Button(outer, text='Convert files', command=self.start_conversion)
        self.convert_btn.pack(fill='x', ipady=6, pady=(8, 10))
        ttk.Progressbar(outer, maximum=100, variable=self.progress).pack(fill='x')
        ttk.Label(outer, textvariable=self.status, wraplength=690).pack(anchor='w', pady=(8, 0))
        ttk.Label(outer, text='PDF → image: each page becomes a separate file. Animated images: first frame only.', foreground='#555').pack(anchor='w', pady=(8, 0))

    def add_files(self):
        paths = filedialog.askopenfilenames(title='Choose files', filetypes=[('Supported files', '*.pdf *.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif'), ('All files', '*.*')])
        existing = set(self.files)
        for raw in paths:
            path = Path(raw)
            if path.suffix.lower() in IMAGE_EXTENSIONS | PDF_EXTENSIONS and path not in existing:
                self.files.append(path)
                self.file_list.insert('end', str(path))
                existing.add(path)
        self.status.set(f'{len(self.files)} file(s) ready.')

    def remove_selected(self):
        for index in reversed(self.file_list.curselection()):
            self.file_list.delete(index)
            self.files.pop(index)
        self.status.set(f'{len(self.files)} file(s) ready.')

    def clear_files(self):
        self.files.clear()
        self.file_list.delete(0, 'end')
        self.status.set('File list cleared.')

    def choose_folder(self):
        folder = filedialog.askdirectory(title='Select output folder')
        if folder:
            self.output_dir.set(folder)

    def start_conversion(self):
        if self.busy:
            return
        if not self.files:
            messagebox.showwarning('No files', 'Please add at least one file.')
            return
        folder = Path(self.output_dir.get()).expanduser()
        if not str(self.output_dir.get()).strip():
            messagebox.showwarning('No folder', 'Choose an output folder.')
            return
        self.busy = True
        self.progress.set(0)
        for button in (self.add_btn, self.remove_btn, self.clear_btn, self.browse_btn, self.convert_btn):
            button.configure(state='disabled')
        self.format_combo.configure(state='disabled')
        self.dpi_combo.configure(state='disabled')
        worker = threading.Thread(target=self.run_conversion, args=(list(self.files), self.target.get(), folder, self.dpi.get()), daemon=True)
        worker.start()

    def run_conversion(self, files: list[Path], target: str, folder: Path, dpi: int):
        count = 0
        errors = []
        for i, path in enumerate(files, 1):
            try:
                generated = convert_file(path, target, folder, dpi)
                count += len(generated)
                self.events.put(('status', f'Converted {path.name} → {len(generated)} file(s)'))
            except Exception as exc:
                errors.append(f'{path.name}: {exc}')
            self.events.put(('progress', i * 100 / len(files)))
        self.events.put(('done', count, errors, str(folder)))

    def poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == 'progress':
                    self.progress.set(event[1])
                elif event[0] == 'status':
                    self.status.set(event[1])
                elif event[0] == 'done':
                    _, count, errors, folder = event
                    self.busy = False
                    for button in (self.add_btn, self.remove_btn, self.clear_btn, self.browse_btn, self.convert_btn):
                        button.configure(state='normal')
                    self.format_combo.configure(state='readonly')
                    self.dpi_combo.configure(state='readonly')
                    self.status.set(f'Done: {count} output file(s); {len(errors)} error(s). Saved in {folder}')
                    if errors:
                        messagebox.showwarning('Conversion results', f'{count} file(s) created.\n\nErrors:\n' + '\n'.join(errors[:15]))
                    else:
                        messagebox.showinfo('Conversion complete', f'{count} file(s) created in:\n{folder}')
        except queue.Empty:
            pass
        self.after(100, self.poll_events)


if __name__ == '__main__':
    ConverterApp().mainloop()
