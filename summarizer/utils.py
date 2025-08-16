import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class FileProcessor:
    """Utility class for processing uploaded files"""
    
    @staticmethod
    def extract_text_from_file(uploaded_file: UploadedFile) -> Dict[str, Any]:
        """
        Extract text content from an uploaded file
        
        Args:
            uploaded_file: Django UploadedFile instance
            
        Returns:
            Dict with success status and extracted text or error message
        """
        try:
            file_extension = FileProcessor._get_file_extension(uploaded_file.name)
            
            if file_extension not in settings.SUMMARIZER_SETTINGS['SUPPORTED_FILE_TYPES']:
                return {
                    'success': False,
                    'error': f'Unsupported file type: {file_extension}. Supported types: {", ".join(settings.SUMMARIZER_SETTINGS["SUPPORTED_FILE_TYPES"])}'
                }
            
            # Check file size
            if uploaded_file.size > settings.SUMMARIZER_SETTINGS['MAX_UPLOAD_SIZE']:
                return {
                    'success': False,
                    'error': f'File size ({uploaded_file.size:,} bytes) exceeds maximum limit ({settings.SUMMARIZER_SETTINGS["MAX_UPLOAD_SIZE"]:,} bytes)'
                }
            
            # Extract text based on file type
            if file_extension == '.txt':
                text = FileProcessor._extract_from_txt(uploaded_file)
            elif file_extension == '.md':
                text = FileProcessor._extract_from_markdown(uploaded_file)
            elif file_extension == '.docx':
                text = FileProcessor._extract_from_docx(uploaded_file)
            else:
                return {
                    'success': False,
                    'error': f'No processor available for {file_extension} files'
                }
            
            if not text.strip():
                return {
                    'success': False,
                    'error': 'No text content found in the uploaded file'
                }
            
            return {
                'success': True,
                'text': text,
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size,
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from file {uploaded_file.name}: {e}")
            return {
                'success': False,
                'error': f'Error processing file: {str(e)}'
            }
    
    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """Get file extension in lowercase"""
        return os.path.splitext(filename.lower())[1]
    
    @staticmethod
    def _extract_from_txt(uploaded_file: UploadedFile) -> str:
        """Extract text from a .txt file"""
        try:
            # Try UTF-8 first
            content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            # Fall back to latin-1 if UTF-8 fails
            uploaded_file.seek(0)
            content = uploaded_file.read().decode('latin-1')
        
        return content
    
    @staticmethod
    def _extract_from_markdown(uploaded_file: UploadedFile) -> str:
        """Extract text from a .md file (same as txt for now)"""
        return FileProcessor._extract_from_txt(uploaded_file)
    
    @staticmethod
    def _extract_from_docx(uploaded_file: UploadedFile) -> str:
        """Extract text from a .docx file"""
        try:
            from docx import Document
            import io
            
            # Read the file content into a BytesIO object
            file_content = io.BytesIO(uploaded_file.read())
            
            # Load the document
            doc = Document(file_content)
            
            # Extract text from all paragraphs
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            return '\n\n'.join(text_parts)
            
        except ImportError:
            raise Exception("python-docx package is required to process .docx files. Please install it with: pip install python-docx")
        except Exception as e:
            raise Exception(f"Error reading .docx file: {str(e)}")
    
    @staticmethod
    def validate_file_upload(uploaded_file: UploadedFile) -> Dict[str, Any]:
        """
        Validate an uploaded file before processing
        
        Args:
            uploaded_file: Django UploadedFile instance
            
        Returns:
            Dict with validation results
        """
        errors = []
        
        # Check file size
        if uploaded_file.size > settings.SUMMARIZER_SETTINGS['MAX_UPLOAD_SIZE']:
            errors.append(f'File size ({uploaded_file.size:,} bytes) exceeds maximum limit ({settings.SUMMARIZER_SETTINGS["MAX_UPLOAD_SIZE"]:,} bytes)')
        
        # Check file extension
        file_extension = FileProcessor._get_file_extension(uploaded_file.name)
        if file_extension not in settings.SUMMARIZER_SETTINGS['SUPPORTED_FILE_TYPES']:
            errors.append(f'Unsupported file type: {file_extension}. Supported types: {", ".join(settings.SUMMARIZER_SETTINGS["SUPPORTED_FILE_TYPES"])}')
        
        # Check filename
        if not uploaded_file.name or uploaded_file.name.strip() == '':
            errors.append('Invalid filename')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'file_size': uploaded_file.size,
            'file_extension': file_extension,
            'filename': uploaded_file.name
        }
