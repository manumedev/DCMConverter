# DICOM to JPEG Converter

A Python tool that converts all DICOM files in a directory to JPEG format. Automatically creates a new folder for converted images under the same parent directory.

## Features

- **Directory Processing**: Designed to process entire directories of DICOM files
- **JPEG Output Only**: All DICOMs converted to high-quality JPEG format
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

### Python API

```python
from dcm_converter import DCMConverter

# Initialize converter
converter = DCMConverter(jpeg_quality=95)

# Convert entire directory (primary use case)
results = converter.convert_directory('/path/to/dicom/files/', 'my_output_folder')

# Convert single file
results = converter.convert_dicom('image.dcm', './output_directory/')
```

## Examples

### Batch Processing (Primary Use Case)
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

### Custom Output Folder
```bash
$ python3 dcm_converter.py /radiology/studies/ct_scan/ -o jpeg_images
Processing DICOM files in directory: /radiology/studies/ct_scan/
Output folder: /radiology/studies/ct_scan/jpeg_images
Converting DICOM files to JPEG: 100%|████████████| 156/156 [08:30<00:00,  3.3s/it]
✓ Successfully converted 156 DICOM files to JPEG
📷 All images saved in: /radiology/studies/ct_scan/jpeg_images/
```

### Single DICOM File
```bash
$ python3 dcm_converter.py chest_xray.dcm -o ./converted/
Processing single DICOM file: chest_xray.dcm
✓ Converted to JPEG: ./converted/chest_xray.jpg
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

### After Conversion:
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