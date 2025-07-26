#!/usr/bin/env python3
"""
Example usage of the DICOM to JPEG Converter tool.

This script demonstrates how to use the DCMConverter class programmatically
with focus on directory processing and automatic folder creation.
"""

import os
import tempfile
from pathlib import Path
from dcm_converter import DCMConverter


def example_directory_conversion():
    """Example: Convert all DICOM files in a directory to JPEG (primary use case)."""
    print("=== Directory Conversion Example (Primary Use Case) ===")
    
    converter = DCMConverter()
    
    # Example directory paths (replace with your actual directories)
    input_directories = [
        "sample_dicom_files",
        "medical_images",
        "patient_data",
        "./dicom_test/"
    ]
    
    for input_dir in input_directories:
        if os.path.exists(input_dir):
            print(f"\nProcessing directory: {input_dir}")
            
            # Option 1: Convert with default folder name
            results = converter.convert_directory(input_dir)
            print(f"✓ Converted {len(results)} files to {input_dir}/converted_jpegs/")
            
            # Option 2: Convert with custom folder name
            results = converter.convert_directory(input_dir, "my_jpeg_images")
            print(f"✓ Converted {len(results)} files to {input_dir}/my_jpeg_images/")
            
            # Show conversion summary
            if results:
                print(f"  📷 {len(results)} DICOM files → JPEG")
                print(f"  📁 All images saved in organized folder")
            
            break  # Process first existing directory
        else:
            print(f"Sample directory {input_dir} not found.")
    
    print("\nTo test with real data:")
    print("1. Create a directory with DICOM files")
    print("2. Run: python3 dcm_converter.py /path/to/your/dicom/directory/")
    print("3. Find converted JPEGs in the new 'converted_jpegs' folder")


def example_custom_output_folders():
    """Example: Using different output folder names for different purposes."""
    print("\n=== Custom Output Folders Example ===")
    
    # Different converter configurations for different scenarios
    
    # High-quality for archival
    archival_converter = DCMConverter(jpeg_quality=98)
    print("High-quality archival converter (JPEG quality: 98)")
    
    # Standard quality for general use
    standard_converter = DCMConverter(jpeg_quality=90)
    print("Standard quality converter (JPEG quality: 90)")
    
    # Compressed for web/sharing
    web_converter = DCMConverter(jpeg_quality=75)
    print("Web-optimized converter (JPEG quality: 75)")
    
    # Example processing scenarios
    scenarios = [
        ("research_data", archival_converter, "archive_quality_jpegs", "High-quality archival"),
        ("clinical_review", standard_converter, "clinical_jpegs", "Clinical review"),
        ("web_sharing", web_converter, "web_ready_jpegs", "Web sharing")
    ]
    
    for dir_name, converter, output_folder, description in scenarios:
        if os.path.exists(dir_name):
            print(f"\n{description}: Processing {dir_name}")
            results = converter.convert_directory(dir_name, output_folder)
            print(f"  Processed {len(results)} files → {dir_name}/{output_folder}/")
        else:
            print(f"  {description}: {dir_name} → {output_folder}/ (example directory)")


def example_directory_analysis():
    """Example: Analyzing directory contents before conversion."""
    print("\n=== Directory Analysis Example ===")
    
    sample_dirs = ["sample_dicom_files", "medical_scans", "patient_studies"]
    
    for sample_dir in sample_dirs:
        if os.path.exists(sample_dir):
            print(f"\nAnalyzing directory: {sample_dir}")
            
            # Analyze DICOM files before conversion
            from pathlib import Path
            import pydicom
            
            dcm_files = []
            # Common DICOM extensions
            for ext in ['.dcm', '.dicom', '.dic']:
                dcm_files.extend(Path(sample_dir).glob(f"*{ext}"))
                dcm_files.extend(Path(sample_dir).glob(f"*{ext.upper()}"))
            
            # Files without extensions (common in DICOM)
            for file_path in Path(sample_dir).iterdir():
                if file_path.is_file() and not file_path.suffix:
                    try:
                        pydicom.dcmread(str(file_path), stop_before_pixels=True)
                        dcm_files.append(file_path)
                    except:
                        pass
            
            if dcm_files:
                print(f"  Found {len(dcm_files)} DICOM files")
                
                single_frame_count = 0
                multi_frame_count = 0
                
                for dcm_file in dcm_files[:5]:  # Analyze first 5 files
                    try:
                        dataset = pydicom.dcmread(str(dcm_file), stop_before_pixels=True)
                        if hasattr(dataset, 'NumberOfFrames') and dataset.NumberOfFrames > 1:
                            multi_frame_count += 1
                            print(f"    🎬 {dcm_file.name}: {dataset.NumberOfFrames} frames (first frame → JPEG)")
                        else:
                            single_frame_count += 1
                            print(f"    📷 {dcm_file.name}: Single frame (→ JPEG)")
                    except Exception as e:
                        print(f"    ⚠ {dcm_file.name}: Could not analyze - {e}")
                
                print(f"  Output: {single_frame_count + multi_frame_count} JPEG files")
                print(f"  Note: Multi-frame DICOMs converted to single JPEG (first frame)")
                
                # Now convert the directory
                converter = DCMConverter()
                results = converter.convert_directory(sample_dir)
                print(f"  ✓ Actually converted: {len(results)} JPEG files")
                print(f"  📁 Saved in: {sample_dir}/converted_jpegs/")
            else:
                print(f"  No DICOM files found in {sample_dir}")
        else:
            print(f"📁 {sample_dir}: Example directory (not present)")


def example_single_file_conversion():
    """Example: Convert a single DICOM file (fallback option)."""
    print("\n=== Single File Conversion Example (Fallback) ===")
    
    # Initialize converter with custom settings
    converter = DCMConverter(jpeg_quality=92)
    
    # Example file paths (replace with your actual DICOM files)
    sample_files = [
        "sample_image.dcm",
        "test_image.dcm", 
        "example.dcm"
    ]
    
    found_file = False
    for dcm_file in sample_files:
        if os.path.exists(dcm_file):
            found_file = True
            # Convert to a specific output directory
            output_dir = "./converted_single/"
            results = converter.convert_dicom(dcm_file, output_dir)
            if results:
                print(f"✓ Successfully converted to JPEG: {results[0]}")
                print(f"📁 Saved in: {output_dir}")
            else:
                print("✗ Conversion failed")
            break
    
    if not found_file:
        print("No sample files found. For single file conversion:")
        print("  python3 dcm_converter.py your_file.dcm -o ./converted/")


def example_batch_processing_workflow():
    """Example: Complete workflow for batch processing."""
    print("\n=== Batch Processing Workflow Example ===")
    
    # Simulate a complete workflow
    workflow_steps = [
        "1. Organize DICOM files in directories by study/patient",
        "2. Run converter on each directory",
        "3. Verify output and organize converted JPEGs",
        "4. Archive or distribute as needed"
    ]
    
    print("Typical batch processing workflow:")
    for step in workflow_steps:
        print(f"  {step}")
    
    print("\nExample commands for workflow:")
    print("  # Step 1: Already organized")
    print("  # Step 2: Convert each directory")
    print("  python3 dcm_converter.py /studies/patient_001/ -o patient_001_jpegs")
    print("  python3 dcm_converter.py /studies/patient_002/ -o patient_002_jpegs")
    print("  python3 dcm_converter.py /studies/patient_003/ -o patient_003_jpegs")
    print("  # Step 3: Check output folders")
    print("  # Step 4: Archive or share the JPEG folders")
    
    # Example of programmatic batch processing
    print("\nProgrammatic batch processing:")
    
    study_directories = ["study_001", "study_002", "study_003"]
    converter = DCMConverter(jpeg_quality=95)
    
    total_converted = 0
    for study_dir in study_directories:
        if os.path.exists(study_dir):
            print(f"  Processing {study_dir}...")
            results = converter.convert_directory(study_dir, f"{study_dir}_jpegs")
            total_converted += len(results)
            print(f"    ✓ {len(results)} files converted")
        else:
            print(f"  📁 {study_dir}: Example directory (not present)")
    
    print(f"\nTotal files processed: {total_converted}")


def main():
    """Run all examples with emphasis on directory processing and folder organization."""
    print("DICOM to JPEG Converter - Usage Examples")
    print("Directory Processing with Automatic Folder Creation")
    print("=" * 65)
    
    try:
        # Primary use case first
        example_directory_conversion()
        example_custom_output_folders()
        example_directory_analysis()
        example_batch_processing_workflow()
        
        # Single file as fallback
        example_single_file_conversion()
        
        print("\n" + "=" * 65)
        print("Examples completed!")
        print("\nPrimary Usage (Directory Processing):")
        print("1. Organize your DICOM files in a directory")
        print("2. Run: python3 dcm_converter.py /path/to/your/dicom/directory/")
        print("3. Find converted JPEGs in the auto-created 'converted_jpegs' folder")
        print("4. All original DICOM files remain unchanged")
        print("\nKey Benefits:")
        print("✓ Automatic folder creation keeps files organized")
        print("✓ Original DICOMs preserved")
        print("✓ All outputs are standard JPEG format")
        print("✓ Multi-frame DICOMs handled intelligently")
        
    except ImportError as e:
        print(f"\n✗ Missing dependency: {e}")
        print("Please install dependencies with: pip3 install -r requirements.txt")
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")


if __name__ == "__main__":
    main() 