#!/usr/bin/env python3
"""
DICOM to JPEG Converter Tool

Converts all DICOM files in a directory to JPEG format.
Automatically creates a new folder for converted images.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Union, List
import numpy as np
from PIL import Image
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
from tqdm import tqdm


class DCMConverter:
    """DICOM to JPEG converter for directory processing."""
    
    def __init__(self, jpeg_quality: int = 95):
        """
        Initialize the converter.
        
        Args:
            jpeg_quality: JPEG compression quality (1-100)
        """
        self.jpeg_quality = jpeg_quality
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('DCMConverter')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _normalize_pixel_array(self, pixel_array: np.ndarray, dataset: pydicom.Dataset) -> np.ndarray:
        """
        Normalize pixel array for display with improved handling for various DICOM formats.
        
        Args:
            pixel_array: Raw pixel data from DICOM
            dataset: DICOM dataset containing metadata
            
        Returns:
            Normalized pixel array suitable for image conversion
        """
        # Make a copy to avoid modifying original data
        pixel_array = pixel_array.copy()
        
        # Handle different data types and ensure we're working with the right format
        if pixel_array.dtype in [np.uint16, np.int16]:
            # For 16-bit data, we need to be more careful with normalization
            self.logger.debug(f"Processing 16-bit data, shape: {pixel_array.shape}, dtype: {pixel_array.dtype}")
        
        # Apply VOI LUT (Value of Interest Look-Up Table) if available
        try:
            # Try to apply VOI LUT for proper windowing
            pixel_array = apply_voi_lut(pixel_array, dataset)
            self.logger.debug("Applied VOI LUT successfully")
        except Exception as e:
            self.logger.debug(f"Could not apply VOI LUT: {e}, proceeding with manual normalization")
            
            # Manual windowing if VOI LUT fails
            if hasattr(dataset, 'WindowCenter') and hasattr(dataset, 'WindowWidth'):
                try:
                    # Handle multiple window values (take first if multiple)
                    window_center = dataset.WindowCenter
                    window_width = dataset.WindowWidth
                    
                    if isinstance(window_center, (list, tuple)):
                        window_center = window_center[0]
                    if isinstance(window_width, (list, tuple)):
                        window_width = window_width[0]
                    
                    # Apply manual windowing
                    img_min = window_center - window_width // 2
                    img_max = window_center + window_width // 2
                    pixel_array = np.clip(pixel_array, img_min, img_max)
                    self.logger.debug(f"Applied manual windowing: center={window_center}, width={window_width}")
                except Exception as e:
                    self.logger.debug(f"Manual windowing failed: {e}")
        
        # Handle different photometric interpretations
        photometric = getattr(dataset, 'PhotometricInterpretation', '')
        
        if photometric == 'MONOCHROME1':
            # Invert for MONOCHROME1 (0 = white, max = black)
            pixel_array = np.max(pixel_array) - pixel_array
            self.logger.debug("Inverted pixel values for MONOCHROME1")
        
        # Robust normalization to 0-255 range
        if pixel_array.dtype != np.uint8:
            # Handle different bit depths with better normalization
            pixel_min = np.min(pixel_array)
            pixel_max = np.max(pixel_array)
            
            self.logger.debug(f"Pixel range before normalization: {pixel_min} to {pixel_max}")
            
            if pixel_max > pixel_min:
                # Use float64 for better precision during normalization
                pixel_array = pixel_array.astype(np.float64)
                pixel_array = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255.0)
                pixel_array = np.clip(pixel_array, 0, 255).astype(np.uint8)
            else:
                # Handle edge case where all pixels have the same value
                self.logger.warning("All pixels have the same value, creating blank image")
                pixel_array = np.full_like(pixel_array, 128, dtype=np.uint8)
        
        self.logger.debug(f"Final pixel array shape: {pixel_array.shape}, dtype: {pixel_array.dtype}")
        return pixel_array
    
    def _extract_frames(self, dataset: pydicom.Dataset) -> List[np.ndarray]:
        """
        Extract all frames from a DICOM dataset with improved error handling.
        
        Args:
            dataset: DICOM dataset
            
        Returns:
            List of normalized frame arrays
        """
        try:
            # Get pixel array with better error handling
            pixel_array = dataset.pixel_array
            self.logger.debug(f"Original pixel array shape: {pixel_array.shape}, dtype: {pixel_array.dtype}")
            
            # Handle different pixel array shapes more robustly
            if len(pixel_array.shape) == 2:
                # Single frame (Height, Width)
                frames = [pixel_array]
                self.logger.debug("Detected single frame DICOM")
            elif len(pixel_array.shape) == 3:
                # Could be multi-frame or color image
                if pixel_array.shape[2] == 3:
                    # RGB color image (Height, Width, 3)
                    frames = [pixel_array]
                    self.logger.debug("Detected RGB color image")
                elif pixel_array.shape[0] < pixel_array.shape[1] and pixel_array.shape[0] < pixel_array.shape[2]:
                    # Multi-frame: (Frames, Height, Width)
                    frames = [pixel_array[i] for i in range(pixel_array.shape[0])]
                    self.logger.debug(f"Detected multi-frame DICOM with {pixel_array.shape[0]} frames")
                else:
                    # Might be (Height, Width, Frames) - less common but possible
                    if pixel_array.shape[2] > 3:
                        frames = [pixel_array[:, :, i] for i in range(pixel_array.shape[2])]
                        self.logger.debug(f"Detected multi-frame DICOM (alternative format) with {pixel_array.shape[2]} frames")
                    else:
                        # Treat as single frame
                        frames = [pixel_array]
                        self.logger.debug("Treating 3D array as single frame")
            elif len(pixel_array.shape) == 4:
                # 4D array: (Frames, Height, Width, Channels) or similar
                if pixel_array.shape[3] == 1:
                    # Grayscale frames with singleton dimension
                    frames = [pixel_array[i, :, :, 0] for i in range(pixel_array.shape[0])]
                elif pixel_array.shape[3] == 3:
                    # RGB frames
                    frames = [pixel_array[i] for i in range(pixel_array.shape[0])]
                else:
                    # Take first frame only
                    frames = [pixel_array[0]]
                self.logger.debug(f"Detected 4D pixel array, extracted {len(frames)} frames")
            else:
                raise ValueError(f"Unsupported pixel array shape: {pixel_array.shape}")
            
            # Normalize each frame
            normalized_frames = []
            for i, frame in enumerate(frames):
                try:
                    normalized_frame = self._normalize_pixel_array(frame, dataset)
                    normalized_frames.append(normalized_frame)
                    self.logger.debug(f"Successfully normalized frame {i+1}/{len(frames)}")
                except Exception as e:
                    self.logger.error(f"Failed to normalize frame {i+1}: {e}")
                    continue
            
            if not normalized_frames:
                raise ValueError("No frames could be successfully normalized")
            
            return normalized_frames
            
        except Exception as e:
            self.logger.error(f"Error extracting frames: {e}")
            # Try alternative pixel data access methods
            try:
                # Some DICOMs need different handling
                if hasattr(dataset, 'PixelData'):
                    self.logger.debug("Trying alternative pixel data access")
                    # Force pixel data loading
                    dataset.decompress()
                    pixel_array = dataset.pixel_array
                    return self._extract_frames(dataset)  # Recursive call after decompression
            except:
                pass
            
            raise ValueError(f"Could not extract pixel data: {e}")
    
    def _frame_to_pil_image(self, frame: np.ndarray) -> Image.Image:
        """
        Convert numpy array to PIL Image with improved handling.
        
        Args:
            frame: Normalized frame array
            
        Returns:
            PIL Image
        """
        self.logger.debug(f"Converting frame to PIL image, shape: {frame.shape}, dtype: {frame.dtype}")
        
        # Ensure frame is in the right format
        if frame.dtype != np.uint8:
            # Convert to uint8 if not already
            frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        # Handle different frame shapes
        if len(frame.shape) == 2:
            # Grayscale image
            pil_image = Image.fromarray(frame, mode='L')
            self.logger.debug("Created grayscale PIL image")
        elif len(frame.shape) == 3:
            if frame.shape[2] == 3:
                # RGB image
                pil_image = Image.fromarray(frame, mode='RGB')
                self.logger.debug("Created RGB PIL image")
            elif frame.shape[2] == 1:
                # Grayscale with singleton dimension
                frame_2d = frame[:, :, 0]
                pil_image = Image.fromarray(frame_2d, mode='L')
                self.logger.debug("Created grayscale PIL image from 3D array")
            else:
                # Convert to grayscale by averaging channels
                frame_2d = np.mean(frame, axis=2).astype(np.uint8)
                pil_image = Image.fromarray(frame_2d, mode='L')
                self.logger.debug("Created grayscale PIL image by averaging channels")
        else:
            raise ValueError(f"Cannot convert frame with shape {frame.shape} to PIL image")
        
        # Verify the image was created correctly
        if pil_image.size[0] == 0 or pil_image.size[1] == 0:
            raise ValueError("Created image has zero width or height")
        
        self.logger.debug(f"Successfully created PIL image with size: {pil_image.size}")
        return pil_image
    
    def convert_dicom(self, dcm_path: Union[str, Path], output_dir: Union[str, Path]) -> List[str]:
        """
        Convert a DICOM file to JPEG(s).
        
        Args:
            dcm_path: Path to the DICOM file
            output_dir: Output directory
            
        Returns:
            List of output file paths if successful, empty list otherwise
        """
        dcm_path = Path(dcm_path)
        output_dir = Path(output_dir)
        
        if not dcm_path.exists():
            self.logger.error(f"File not found: {dcm_path}")
            return []
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Read DICOM file with detailed logging
            self.logger.debug(f"Reading DICOM file: {dcm_path}")
            dataset = pydicom.dcmread(str(dcm_path))
            
            # Log DICOM metadata for debugging
            self.logger.debug(f"DICOM SOP Class UID: {getattr(dataset, 'SOPClassUID', 'Unknown')}")
            self.logger.debug(f"Transfer Syntax UID: {getattr(dataset, 'file_meta', {}).get('TransferSyntaxUID', 'Unknown')}")
            self.logger.debug(f"Photometric Interpretation: {getattr(dataset, 'PhotometricInterpretation', 'Unknown')}")
            self.logger.debug(f"Bits Allocated: {getattr(dataset, 'BitsAllocated', 'Unknown')}")
            self.logger.debug(f"Bits Stored: {getattr(dataset, 'BitsStored', 'Unknown')}")
            self.logger.debug(f"Pixel Representation: {getattr(dataset, 'PixelRepresentation', 'Unknown')}")
            self.logger.debug(f"Number of Frames: {getattr(dataset, 'NumberOfFrames', 1)}")
            
            if hasattr(dataset, 'Rows') and hasattr(dataset, 'Columns'):
                self.logger.debug(f"Image dimensions: {dataset.Rows} x {dataset.Columns}")
            
            # Check if pixel data exists
            if not hasattr(dataset, 'pixel_array'):
                self.logger.error(f"No pixel data found in: {dcm_path}")
                return []
            
            # Try to get basic info about pixel data before processing
            try:
                test_array = dataset.pixel_array
                self.logger.debug(f"Pixel array shape: {test_array.shape}, dtype: {test_array.dtype}")
                self.logger.debug(f"Pixel value range: {np.min(test_array)} to {np.max(test_array)}")
            except Exception as e:
                self.logger.error(f"Cannot access pixel array: {e}")
                return []
            
            # Extract frames
            frames = self._extract_frames(dataset)
            
            if not frames:
                self.logger.error(f"No valid frames extracted from: {dcm_path}")
                return []
            
            base_name = dcm_path.stem
            output_paths = []
            
            if len(frames) == 1:
                # Single frame -> Single JPEG
                output_path = output_dir / f"{base_name}.jpg"
                try:
                    pil_image = self._frame_to_pil_image(frames[0])
                    
                    # Additional validation before saving
                    if pil_image.size[0] < 10 or pil_image.size[1] < 10:
                        self.logger.warning(f"Image is very small: {pil_image.size}")
                    
                    pil_image.save(
                        output_path,
                        'JPEG',
                        quality=self.jpeg_quality,
                        optimize=True
                    )
                    output_paths.append(str(output_path))
                    self.logger.info(f"Converted to JPEG: {output_path} (size: {pil_image.size})")
                except Exception as e:
                    self.logger.error(f"Failed to save JPEG: {e}")
                    return []
            
            else:
                # Multi-frame -> Single JPEG (first frame)
                output_path = output_dir / f"{base_name}.jpg"
                try:
                    pil_image = self._frame_to_pil_image(frames[0])
                    
                    # Additional validation before saving
                    if pil_image.size[0] < 10 or pil_image.size[1] < 10:
                        self.logger.warning(f"Image is very small: {pil_image.size}")
                    
                    pil_image.save(
                        output_path,
                        'JPEG',
                        quality=self.jpeg_quality,
                        optimize=True
                    )
                    output_paths.append(str(output_path))
                    self.logger.info(f"Converted multi-frame DICOM to JPEG (first frame): {output_path} (size: {pil_image.size})")
                    self.logger.debug(f"Original had {len(frames)} frames, saved first frame only")
                except Exception as e:
                    self.logger.error(f"Failed to save JPEG from multi-frame: {e}")
                    return []
                
                # Option 2: Uncomment below to save all frames as separate JPEGs
                # for i, frame in enumerate(frames):
                #     output_path = output_dir / f"{base_name}_frame_{i+1:03d}.jpg"
                #     try:
                #         pil_image = self._frame_to_pil_image(frame)
                #         pil_image.save(
                #             output_path,
                #             'JPEG',
                #             quality=self.jpeg_quality,
                #             optimize=True
                #         )
                #         output_paths.append(str(output_path))
                #         self.logger.debug(f"Saved frame {i+1}/{len(frames)}: {output_path}")
                #     except Exception as e:
                #         self.logger.error(f"Failed to save frame {i+1}: {e}")
                #         continue
            
            return output_paths
        
        except Exception as e:
            self.logger.error(f"Error converting {dcm_path}: {str(e)}")
            
            # Additional diagnostic information
            try:
                self.logger.debug("Attempting to gather diagnostic information...")
                dataset = pydicom.dcmread(str(dcm_path), stop_before_pixels=True)
                self.logger.debug(f"DICOM file can be read (header only)")
                self.logger.debug(f"Modality: {getattr(dataset, 'Modality', 'Unknown')}")
                self.logger.debug(f"Manufacturer: {getattr(dataset, 'Manufacturer', 'Unknown')}")
                
                # Try to identify transfer syntax issues
                if hasattr(dataset, 'file_meta') and hasattr(dataset.file_meta, 'TransferSyntaxUID'):
                    ts_uid = dataset.file_meta.TransferSyntaxUID
                    self.logger.debug(f"Transfer Syntax: {ts_uid}")
                    
                    # Common problematic transfer syntaxes
                    if 'JPEG' in str(ts_uid):
                        self.logger.error("JPEG compressed DICOM detected - may need additional codec support")
                    elif 'RLE' in str(ts_uid):
                        self.logger.error("RLE compressed DICOM detected - may need additional codec support")
            except Exception as diag_e:
                self.logger.debug(f"Could not gather diagnostic info: {diag_e}")
            
            return []
    
    def diagnose_dicom(self, dcm_path: Union[str, Path]) -> bool:
        """
        Diagnose a DICOM file to identify potential conversion issues.
        
        Args:
            dcm_path: Path to the DICOM file
            
        Returns:
            True if file appears convertible, False otherwise
        """
        dcm_path = Path(dcm_path)
        
        if not dcm_path.exists():
            print(f"❌ File not found: {dcm_path}")
            return False
        
        print(f"🔍 Diagnosing DICOM file: {dcm_path}")
        print("=" * 60)
        
        try:
            # Read DICOM header
            dataset = pydicom.dcmread(str(dcm_path), stop_before_pixels=True)
            
            # Basic file info
            print("📋 Basic Information:")
            print(f"   Modality: {getattr(dataset, 'Modality', 'Unknown')}")
            print(f"   Manufacturer: {getattr(dataset, 'Manufacturer', 'Unknown')}")
            print(f"   SOP Class: {getattr(dataset, 'SOPClassUID', 'Unknown')}")
            
            # Transfer syntax
            if hasattr(dataset, 'file_meta') and hasattr(dataset.file_meta, 'TransferSyntaxUID'):
                ts_uid = str(dataset.file_meta.TransferSyntaxUID)
                print(f"   Transfer Syntax: {ts_uid}")
                
                # Check for problematic transfer syntaxes
                if 'JPEG' in ts_uid:
                    print("   ⚠️  JPEG compressed - may need additional codecs")
                elif 'RLE' in ts_uid:
                    print("   ⚠️  RLE compressed - may need additional codecs")
                elif '1.2.840.10008.1.2' in ts_uid:
                    print("   ✅ Uncompressed - should work well")
            
            # Image properties
            print("\n🖼️  Image Properties:")
            if hasattr(dataset, 'Rows') and hasattr(dataset, 'Columns'):
                print(f"   Dimensions: {dataset.Columns} x {dataset.Rows}")
            else:
                print("   ❌ No image dimensions found")
                return False
            
            print(f"   Bits Allocated: {getattr(dataset, 'BitsAllocated', 'Unknown')}")
            print(f"   Bits Stored: {getattr(dataset, 'BitsStored', 'Unknown')}")
            print(f"   Pixel Representation: {getattr(dataset, 'PixelRepresentation', 'Unknown')}")
            print(f"   Photometric Interpretation: {getattr(dataset, 'PhotometricInterpretation', 'Unknown')}")
            
            # Frame info
            num_frames = getattr(dataset, 'NumberOfFrames', 1)
            print(f"   Number of Frames: {num_frames}")
            if num_frames > 1:
                print("   🎬 Multi-frame DICOM (will convert first frame only)")
            
            # Window/Level info
            if hasattr(dataset, 'WindowCenter') and hasattr(dataset, 'WindowWidth'):
                wc = dataset.WindowCenter
                ww = dataset.WindowWidth
                if isinstance(wc, (list, tuple)):
                    wc = wc[0]
                if isinstance(ww, (list, tuple)):
                    ww = ww[0]
                print(f"   Window Center/Width: {wc}/{ww}")
            else:
                print("   ℹ️  No windowing information found")
            
            # Try to access pixel data
            print("\n🔬 Pixel Data Analysis:")
            try:
                # Read with pixel data
                dataset_full = pydicom.dcmread(str(dcm_path))
                pixel_array = dataset_full.pixel_array
                
                print(f"   ✅ Pixel data accessible")
                print(f"   Shape: {pixel_array.shape}")
                print(f"   Data type: {pixel_array.dtype}")
                print(f"   Value range: {np.min(pixel_array)} to {np.max(pixel_array)}")
                
                # Check for common issues
                if pixel_array.size == 0:
                    print("   ❌ Empty pixel array")
                    return False
                
                if len(pixel_array.shape) < 2:
                    print("   ❌ Invalid pixel array dimensions")
                    return False
                
                if pixel_array.shape[0] == 1 or pixel_array.shape[1] == 1:
                    print("   ⚠️  Very thin image - this might appear as a line")
                    print("   💡 This could be the cause of your vertical line issue!")
                
                if np.all(pixel_array == pixel_array.flat[0]):
                    print("   ⚠️  All pixels have the same value")
                
                # Test normalization
                try:
                    if len(pixel_array.shape) == 3 and pixel_array.shape[0] < min(pixel_array.shape[1], pixel_array.shape[2]):
                        test_frame = pixel_array[0]
                    else:
                        test_frame = pixel_array
                    
                    normalized = self._normalize_pixel_array(test_frame, dataset_full)
                    print(f"   ✅ Normalization successful")
                    print(f"   Normalized range: {np.min(normalized)} to {np.max(normalized)}")
                    
                    # Test PIL conversion
                    pil_image = self._frame_to_pil_image(normalized)
                    print(f"   ✅ PIL conversion successful")
                    print(f"   Final image size: {pil_image.size}")
                    
                    if pil_image.size[0] < 10 or pil_image.size[1] < 10:
                        print("   ⚠️  Very small image size - may appear as a line")
                    
                    return True
                    
                except Exception as e:
                    print(f"   ❌ Processing failed: {e}")
                    return False
                
            except Exception as e:
                print(f"   ❌ Cannot access pixel data: {e}")
                
                # Additional help for compressed formats
                if 'JPEG' in str(getattr(dataset.file_meta, 'TransferSyntaxUID', '')):
                    print("   💡 Try installing: pip install pillow-jpeg-ls gdcm-python")
                elif 'RLE' in str(getattr(dataset.file_meta, 'TransferSyntaxUID', '')):
                    print("   💡 Try installing: pip install gdcm-python")
                
                return False
                
        except Exception as e:
            print(f"❌ Error reading DICOM file: {e}")
            return False
    
    def convert_directory(self, input_dir: Union[str, Path], output_folder_name: str = "converted_jpegs") -> List[str]:
        """
        Convert all DICOM files in a directory to JPEGs.
        
        Args:
            input_dir: Directory containing DICOM files
            output_folder_name: Name of the output folder to create
            
        Returns:
            List of successfully converted file paths
        """
        input_dir = Path(input_dir)
        
        if not input_dir.is_dir():
            self.logger.error(f"Directory not found: {input_dir}")
            return []
        
        # Create output directory under the same parent as input
        output_dir = input_dir / output_folder_name
        
        # Find DICOM files (common extensions)
        dcm_extensions = {'.dcm', '.dicom', '.dic'}
        dcm_files = []
        
        for ext in dcm_extensions:
            dcm_files.extend(input_dir.glob(f"*{ext}"))
            dcm_files.extend(input_dir.glob(f"*{ext.upper()}"))
        
        # Also check files without extensions (common in DICOM)
        for file_path in input_dir.iterdir():
            if file_path.is_file() and not file_path.suffix and file_path.name != output_folder_name:
                try:
                    # Try to read as DICOM
                    pydicom.dcmread(str(file_path), stop_before_pixels=True)
                    dcm_files.append(file_path)
                except:
                    pass
        
        if not dcm_files:
            self.logger.warning(f"No DICOM files found in: {input_dir}")
            return []
        
        self.logger.info(f"Found {len(dcm_files)} DICOM files")
        self.logger.info(f"Output directory: {output_dir}")
        
        successful_conversions = []
        
        # Convert with progress bar
        for dcm_file in tqdm(dcm_files, desc="Converting DICOM files to JPEG"):
            results = self.convert_dicom(dcm_file, output_dir)
            successful_conversions.extend(results)
        
        self.logger.info(f"Successfully converted {len(successful_conversions)} files")
        return successful_conversions


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="Convert DICOM files in a directory to JPEG format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/dicom/directory/      # Convert all DICOM files to JPEG
  %(prog)s ./medical_images/              # Convert files in local directory
  %(prog)s ~/dicom_data/ -o my_jpegs      # Custom output folder name
  %(prog)s /data/dicoms/ -q 90            # Custom JPEG quality
  %(prog)s image.dcm -o ./converted/      # Convert single file
  %(prog)s image.dcm --diagnose           # Diagnose DICOM file issues
        """
    )
    
    parser.add_argument(
        'input',
        help='Directory containing DICOM files (or single DICOM file)'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='converted_jpegs',
        help='Output folder name (default: converted_jpegs)'
    )
    
    parser.add_argument(
        '-q', '--quality',
        type=int,
        default=95,
        choices=range(1, 101),
        metavar='1-100',
        help='JPEG quality (1-100, default: 95)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--diagnose',
        action='store_true',
        help='Diagnose DICOM file(s) for conversion issues without converting'
    )
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger('DCMConverter').setLevel(logging.DEBUG)
    
    # Initialize converter
    converter = DCMConverter(jpeg_quality=args.quality)
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    try:
        if args.diagnose:
            # Diagnostic mode
            if input_path.is_file():
                # Diagnose single file
                print("🔍 DICOM Diagnostic Mode")
                print("=" * 50)
                result = converter.diagnose_dicom(input_path)
                if result:
                    print("\n✅ DICOM file appears to be convertible")
                    print("If you're still seeing issues, try running with -v for verbose output")
                else:
                    print("\n❌ DICOM file has issues that may prevent conversion")
                    print("See the diagnostic information above for details")
            
            elif input_path.is_dir():
                # Diagnose directory
                print("🔍 DICOM Directory Diagnostic Mode")
                print("=" * 50)
                
                # Find DICOM files
                dcm_extensions = {'.dcm', '.dicom', '.dic'}
                dcm_files = []
                
                for ext in dcm_extensions:
                    dcm_files.extend(input_path.glob(f"*{ext}"))
                    dcm_files.extend(input_path.glob(f"*{ext.upper()}"))
                
                # Also check files without extensions
                for file_path in input_path.iterdir():
                    if file_path.is_file() and not file_path.suffix:
                        try:
                            pydicom.dcmread(str(file_path), stop_before_pixels=True)
                            dcm_files.append(file_path)
                        except:
                            pass
                
                if not dcm_files:
                    print(f"❌ No DICOM files found in: {input_path}")
                    sys.exit(1)
                
                print(f"Found {len(dcm_files)} DICOM files to diagnose\n")
                
                success_count = 0
                for i, dcm_file in enumerate(dcm_files[:5]):  # Limit to first 5 for readability
                    print(f"File {i+1}/{min(len(dcm_files), 5)}: {dcm_file.name}")
                    result = converter.diagnose_dicom(dcm_file)
                    if result:
                        success_count += 1
                    print()
                
                if len(dcm_files) > 5:
                    print(f"... and {len(dcm_files) - 5} more files")
                
                print(f"📊 Summary: {success_count}/{min(len(dcm_files), 5)} files appear convertible")
                
                if success_count == 0:
                    print("❌ No files appear to be convertible")
                    print("Common solutions:")
                    print("  - Install additional codecs: pip install gdcm-python")
                    print("  - Check if files are valid DICOM with pixel data")
                elif success_count < min(len(dcm_files), 5):
                    print("⚠️  Some files may have conversion issues")
                    print("Run diagnosis on individual problem files for more details")
                else:
                    print("✅ All tested files should convert successfully")
                    print("If you're still having issues, try converting with -v for verbose output")
            
            return
        
        # Normal conversion mode
        if input_path.is_dir():
            # Convert directory (primary use case)
            print(f"Processing DICOM files in directory: {input_path}")
            print(f"Output folder: {input_path}/{args.output}")
            
            results = converter.convert_directory(input_path, args.output)
            if results:
                print(f"✓ Successfully converted {len(results)} DICOM files to JPEG")
                print(f"📷 All images saved in: {input_path}/{args.output}/")
                    
                if args.verbose:
                    print("\nConverted files:")
                    for result in results:
                        print(f"  {result}")
            else:
                print("✗ No files were converted successfully")
                print("  Make sure the directory contains valid DICOM files with pixel data")
                print("  Run with --diagnose to identify issues: python3 dcm_converter.py /path/to/dir/ --diagnose")
                sys.exit(1)
                
        elif input_path.is_file():
            # Convert single file (fallback option)
            print(f"Processing single DICOM file: {input_path}")
            
            if args.output == 'converted_jpegs':
                # For single file, use parent directory + output folder
                output_dir = input_path.parent / args.output
            else:
                output_dir = Path(args.output)
            
            results = converter.convert_dicom(input_path, output_dir)
            if results:
                print(f"✓ Converted to JPEG: {results[0]}")
            else:
                print("✗ Conversion failed")
                print("  Make sure the file is a valid DICOM with pixel data")
                print("  Run with --diagnose to identify issues: python3 dcm_converter.py file.dcm --diagnose")
                sys.exit(1)
        
        else:
            print(f"Error: Invalid input path: {input_path}")
            print("Please provide a directory containing DICOM files or a single DICOM file")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n✗ Conversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main() 