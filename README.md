# DICOM to JPEG Converter

A Python tool that converts all DICOM files in a directory to JPEG format. Automatically creates a new folder for converted images under the same parent directory. Optionally creates PDFs from the converted images with automatic size management.

## Features

- **Directory Processing**: Designed to process entire directories of DICOM files
- **JPEG Output**: All DICOMs converted to high-quality JPEG format
- **PDF Creation**: Create PDFs from converted JPEG images with size management
- **Automatic Size Management**: Splits PDFs when they exceed specified size limit (default: 512MB)
- **Automatic Folder Creation**: Creates a new folder for converted images
- **Multi-frame Handling**: Converts multi-frame DICOMs to JPEG (first frame)
- **Robust Processing**: Handles various DICOM formats and pixel data types
- **Batch Processing**: Efficiently convert hundreds of DICOM files at once
- **VOI LUT Support**: Properly applies windowing/leveling information
- **Photometric Interpretation**: Correctly handles MONOCHROME1/MONOCHROME2/RGB
- **Progress Tracking**: Visual progress bar for batch operations
- **Error Handling**: Graceful handling of corrupted or unsupported files

## Installation

1. **Clone or download this repository**
2. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

## Usage

### Command Line Interface

#### Convert all DICOM files in a directory (primary use case):
```bash
python3 dcm_converter.py /path/to/dicom/directory/
```

#### Convert files in current directory:
```bash
python3 dcm_converter.py ./
```

#### Custom output folder name:
```bash
python3 dcm_converter.py ~/dicom_data/ -o my_jpegs
```

#### Custom JPEG quality:
```bash
python3 dcm_converter.py /medical/scans/ -q 90
```

#### Convert single file:
```bash
python3 dcm_converter.py image.dcm -o ./converted/
```

#### Create PDFs from converted images:
```bash
python3 dcm_converter.py /dicom/files/ --pdf
```

#### Create PDFs with custom size limit:
```bash
python3 dcm_converter.py /dicom/files/ --pdf --pdf-size 256
```

#### Verbose output:
```bash
python3 dcm_converter.py /dicom/files/ -v
```

#### Diagnose DICOM issues:
```bash
python3 dcm_converter.py problematic_file.dcm --diagnose
```

### Command Line Options

- `input`: Directory containing DICOM files (or single DICOM file)
- `-o, --output`: Output folder name (default: converted_jpegs)
- `-q, --quality`: JPEG quality 1-100 (default: 95)
- `-v, --verbose`: Enable verbose logging and show detailed file list
- `--diagnose`: Diagnose DICOM file(s) for conversion issues without converting
- `--pdf`: Create PDF files from converted JPEG images
- `--pdf-size`: Maximum size per PDF file in MB (default: 512)

### Python API

```python
from dcm_converter import DCMConverter

# Initialize converter
converter = DCMConverter(jpeg_quality=95)

# Convert entire directory to JPEGs only
results = converter.convert_directory('/path/to/dicom/files/', 'my_output_folder')

# Convert to JPEGs and create PDFs
jpeg_files, pdf_files = converter.convert_directory_with_pdf(
    '/path/to/dicom/files/', 
    'my_output_folder',
    create_pdf=True,
    pdf_max_size_mb=512
)

# Convert single file
results = converter.convert_dicom('image.dcm', './output_directory/')

# Create PDFs from existing JPEG files
pdf_files = converter.create_pdfs_from_jpegs(
    jpeg_file_list, 
    './output_directory/', 
    'my_document',
    max_size_mb=256
)
```

## Examples

### Batch Processing with PDF Creation
```bash
$ python3 dcm_converter.py /medical/imaging/patient_001/ --pdf
Processing DICOM files in directory: /medical/imaging/patient_001/
Output folder: /medical/imaging/patient_001/converted_jpegs
PDF creation enabled (max size: 512MB per PDF)
2024-01-15 10:30:25 - DCMConverter - INFO - Found 24 DICOM files
Converting DICOM files to JPEG: 100%|████████████| 24/24 [01:15<00:00,  3.1s/it]
✓ Successfully converted 24 DICOM files to JPEG
📷 All images saved in: /medical/imaging/patient_001/converted_jpegs/
Creating PDFs from 24 JPEG files
Creating PDFs: 100%|████████████| 24/24 [00:30<00:00,  1.2s/it]
📄 Successfully created 1 PDF file(s):
  📄 patient_001_images_part_001.pdf (423.2MB)
```

### Large Dataset with Multiple PDFs
```bash
$ python3 dcm_converter.py /radiology/ct_study_large/ --pdf --pdf-size 256
Processing DICOM files in directory: /radiology/ct_study_large/
PDF creation enabled (max size: 256MB per PDF)
Converting DICOM files to JPEG: 100%|████████████| 156/156 [08:30<00:00,  3.3s/it]
✓ Successfully converted 156 DICOM files to JPEG
Creating PDFs: 100%|████████████| 156/156 [02:15<00:00,  1.1s/it]
📄 Successfully created 3 PDF file(s):
  📄 ct_study_large_images_part_001.pdf (255.8MB)
  📄 ct_study_large_images_part_002.pdf (249.3MB)
  📄 ct_study_large_images_part_003.pdf (187.6MB)
```

### Batch Processing (JPEG Only - Original Functionality)
```bash
$ python3 dcm_converter.py /medical/imaging/patient_001/
Processing DICOM files in directory: /medical/imaging/patient_001/
Output folder: /medical/imaging/patient_001/converted_jpegs
2024-01-15 10:30:25 - DCMConverter - INFO - Found 24 DICOM files
2024-01-15 10:30:25 - DCMConverter - INFO - Output directory: /medical/imaging/patient_001/converted_jpegs
Converting DICOM files to JPEG: 100%|████████████| 24/24 [01:15<00:00,  3.1s/it]
2024-01-15 10:31:40 - DCMConverter - INFO - Successfully converted 24 files
✓ Successfully converted 24 DICOM files to JPEG
📷 All images saved in: /medical/imaging/patient_001/converted_jpegs/
```

## Directory Structure

### Before Conversion:
```
patient_data/
├── CT_CHEST/
│   ├── IM_001.dcm
│   ├── IM_002.dcm
│   └── IM_003.dcm
├── CINE_HEART/
│   ├── CINE_001.dcm  (multi-frame)
│   └── CINE_002.dcm  (multi-frame)
└── XRAY/
    ├── CHEST_PA.dcm
    └── CHEST_LAT.dcm
```

### After Conversion (JPEG Only):
```
patient_data/
├── converted_jpegs/          # ← New folder created automatically
│   ├── IM_001.jpg
│   ├── IM_002.jpg
│   ├── IM_003.jpg
│   ├── CINE_001.jpg         # First frame of multi-frame DICOM
│   ├── CINE_002.jpg         # First frame of multi-frame DICOM
│   ├── CHEST_PA.jpg
│   └── CHEST_LAT.jpg
├── CT_CHEST/
│   ├── IM_001.dcm           # Original files remain unchanged
│   ├── IM_002.dcm
│   └── IM_003.dcm
├── CINE_HEART/
│   ├── CINE_001.dcm
│   └── CINE_002.dcm
└── XRAY/
    ├── CHEST_PA.dcm
    └── CHEST_LAT.dcm
```

### After Conversion with PDF Creation:
```
patient_data/
├── converted_jpegs/          # ← New folder created automatically
│   ├── IM_001.jpg
│   ├── IM_002.jpg
│   ├── IM_003.jpg
│   ├── CINE_001.jpg
│   ├── CINE_002.jpg
│   ├── CHEST_PA.jpg
│   ├── CHEST_LAT.jpg
│   ├── patient_data_images_part_001.pdf  # ← PDF files created automatically
│   └── patient_data_images_part_002.pdf  # ← Split if size limit exceeded
├── CT_CHEST/
│   ├── IM_001.dcm           # Original files remain unchanged
│   ├── IM_002.dcm
│   └── IM_003.dcm
├── CINE_HEART/
│   ├── CINE_001.dcm
│   └── CINE_002.dcm
└── XRAY/
    ├── CHEST_PA.dcm
    └── CHEST_LAT.dcm
```

## PDF Features

### **Automatic Size Management**
- PDFs are automatically split when they exceed the specified size limit
- Default limit: 512MB per PDF file
- Customizable with `--pdf-size` option
- Sequential naming: `_part_001.pdf`, `_part_002.pdf`, etc.

### **Image Layout**
- Each JPEG becomes one page in the PDF
- Images are automatically scaled to fit A4 pages
- Maintains aspect ratio with centered positioning
- Includes filename as caption at bottom of each page
- 0.5-inch margins for professional appearance

### **PDF Naming Convention**
- Format: `{directory_name}_images_part_{number}.pdf`
- Example: `patient_001_images_part_001.pdf`
- Sequential numbering for multiple PDFs from same dataset

## Multi-frame DICOM Handling

For multi-frame DICOM files (animations/cine):
- **Default**: Converts only the first frame to JPEG
- **Alternative**: Uncomment code in `convert_dicom()` to save all frames as separate JPEGs

### To save all frames as separate JPEGs:
1. Edit `dcm_converter.py`
2. In the `convert_dicom()` method, uncomment the "Option 2" section
3. Multi-frame files will create: `filename_frame_001.jpg`, `filename_frame_002.jpg`, etc.

## Supported DICOM Features

- **Pixel Data Types**: 8-bit, 16-bit, signed/unsigned integers
- **Photometric Interpretations**: MONOCHROME1, MONOCHROME2, RGB
- **Multi-frame Support**: First frame extraction (configurable for all frames)
- **VOI LUT**: Applies window/level settings when available
- **Compressed Transfer Syntaxes**: Supports various DICOM compression formats

## File Detection

The tool automatically detects DICOM files by:
- File extensions: `.dcm`, `.dicom`, `.dic` (case-insensitive)
- Files without extensions that contain valid DICOM headers
- DICOM magic numbers and metadata validation

## Output Quality

- **JPEG**: Default quality 95% with optimization enabled
- **Pixel Normalization**: Automatic scaling to 0-255 range
- **Aspect Ratio**: Preserved from original DICOM
- **File Size**: Optimized for storage and viewing

## Performance

- **Batch Processing**: Optimized for processing large directories
- **Memory Efficient**: Processes files one at a time to handle large datasets
- **Progress Tracking**: Real-time progress bar shows conversion status
- **Error Recovery**: Continues processing even if individual files fail

## Error Handling

The tool handles various edge cases:
- Corrupted DICOM files
- Missing pixel data
- Unsupported transfer syntaxes
- Invalid file formats
- Permission errors
- Out of memory conditions
- Mixed file types in directories

## Dependencies

- `pydicom>=2.4.0`: DICOM file reading and parsing
- `Pillow>=10.0.0`: Image processing and format conversion
- `numpy>=1.24.0`: Numerical operations on pixel data
- `tqdm>=4.65.0`: Progress bars for batch operations

## License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

## Troubleshooting

### Common Issues

1. **"No DICOM files found"**: Check file extensions and ensure files are valid DICOM
2. **"No pixel data found"**: Some DICOM files may be reports or structured documents
3. **"Unsupported transfer syntax"**: Install additional pydicom pixel data handlers
4. **Memory errors**: Large multi-frame files may require more RAM
5. **Permission denied**: Check file/directory permissions

### Getting Help

If you encounter issues:
1. Run with `-v` flag for verbose output
2. Check that your DICOM files contain pixel data
3. Verify file permissions and disk space
4. Ensure all dependencies are properly installed
5. Test with a small subset of files first 

## Troubleshooting DICOM Conversion Issues

### 🔍 Diagnostic Mode

If you're seeing issues like vertical lines or failed conversions, use the diagnostic mode to identify problems:

```bash
# Diagnose a single DICOM file
python3 dcm_converter.py problematic_file.dcm --diagnose

# Diagnose all DICOM files in a directory
python3 dcm_converter.py /path/to/dicom/directory/ --diagnose
```

The diagnostic tool will analyze:
- DICOM file structure and metadata
- Transfer syntax and compression
- Pixel data accessibility and format
- Image dimensions and properties
- Potential conversion issues

### Common Issues and Solutions

#### 📏 **Vertical Line in Images**
**Cause**: Image has very small dimensions (width or height of 1 pixel)
**Solution**: 
```bash
# First diagnose the file
python3 dcm_converter.py file.dcm --diagnose
# Look for "Very thin image" warnings
```

#### 🗜️ **Compressed DICOM Files**
**Cause**: JPEG or RLE compressed DICOMs need additional codecs
**Solution**:
```bash
pip3 install gdcm-python
# or for JPEG-LS support:
pip3 install pillow-jpeg-ls gdcm-python
```

#### 📊 **Empty or Malformed Images**
**Cause**: Missing pixel data or unsupported format
**Diagnostic**: Use `--diagnose` to check pixel data accessibility
**Solution**: Verify file is a valid DICOM with image data

#### 🔧 **Processing Errors**
**Cause**: Complex DICOM structure or metadata issues
**Solution**:
```bash
# Use verbose mode for detailed error information
python3 dcm_converter.py /path/to/files/ -v
``` 