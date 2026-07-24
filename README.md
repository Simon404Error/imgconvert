# imgconvert

Convert between PDF, ICO, JPG, and PNG formats from the command line.

## Supported conversions

| From  | To           |
|-------|--------------|
| PDF   | JPG, PNG, ICO |
| JPG   | PDF, PNG, ICO |
| PNG   | PDF, JPG, ICO |
| ICO   | PDF, JPG, PNG |

- PDF → image: each page renders at 200 DPI; multi-page PDFs produce one image per page (first page used for single-image targets like JPG/PNG/ICO)
- Image → PDF: preserves original dimensions at 200 DPI
- ICO output: auto-generates standard sizes (256, 128, 64, 48, 32, 16 px)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

**Single file — specify target path:**

```bash
python -m imgconvert convert input.png output.jpg
```

**Single file — specify target format only (auto-names the output):**

```bash
python -m imgconvert convert input.png -f .pdf
```

**Batch convert:**

```bash
python -m imgconvert batch *.png -f .jpg -o ./converted/
```

**Adjust JPEG quality (default 95):**

```bash
python -m imgconvert convert input.png output.jpg -q 85
```
