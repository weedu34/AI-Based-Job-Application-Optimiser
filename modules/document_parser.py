import PyPDF2
import pdfplumber
from docx import Document
import docx2txt
import os
from typing import Dict, Optional, Tuple

class DocumentParser:
    """Handles parsing of PDF, DOCX, and TXT files while preserving structure"""
    
    @staticmethod
    def parse_document(file_path: str) -> Dict[str, any]:
        """
        Parse document and extract text with structure information
        
        Returns:
            Dict containing:
            - text: extracted text content
            - structure: formatting and structure info
            - metadata: document metadata
            - success: boolean indicating success
            - error: error message if failed
        """
        
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return DocumentParser._parse_pdf(file_path)
            elif file_extension == '.docx':
                return DocumentParser._parse_docx(file_path)
            elif file_extension == '.txt':
                return DocumentParser._parse_txt(file_path)
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file format: {file_extension}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error parsing document: {str(e)}'
            }
    
    @staticmethod
    def _parse_pdf(file_path: str) -> Dict[str, any]:
        """Parse PDF file using pdfplumber for better text extraction"""
        
        try:
            text_content = []
            structure_info = {
                'pages': [],
                'fonts': set(),
                'formatting': []
            }
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                        
                        # Extract structure information
                        page_info = {
                            'page_number': page_num,
                            'text_length': len(page_text),
                            'lines': page_text.split('\n')
                        }
                        structure_info['pages'].append(page_info)
            
            return {
                'success': True,
                'text': '\n\n'.join(text_content),
                'structure': structure_info,
                'metadata': {
                    'total_pages': len(structure_info['pages']),
                    'file_type': 'pdf'
                }
            }
            
        except Exception as e:
            # Fallback to PyPDF2 if pdfplumber fails
            try:
                return DocumentParser._parse_pdf_fallback(file_path)
            except:
                return {
                    'success': False,
                    'error': f'Failed to parse PDF: {str(e)}'
                }
    
    @staticmethod
    def _parse_pdf_fallback(file_path: str) -> Dict[str, any]:
        """Fallback PDF parsing using PyPDF2"""
        
        text_content = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                text_content.append(page.extract_text())
        
        return {
            'success': True,
            'text': '\n\n'.join(text_content),
            'structure': {'pages': len(pdf_reader.pages)},
            'metadata': {'total_pages': len(pdf_reader.pages), 'file_type': 'pdf'}
        }
    
    @staticmethod
    def _parse_docx(file_path: str) -> Dict[str, any]:
        """Parse DOCX file preserving structure"""
        
        try:
            # Extract text with python-docx for structure
            doc = Document(file_path)
            
            paragraphs = []
            structure_info = {
                'paragraphs': [],
                'styles': set(),
                'headers': [],
                'formatting': []
            }
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
                    
                    # Store structure information
                    para_info = {
                        'text': para.text,
                        'style': para.style.name if para.style else 'Normal',
                        'alignment': str(para.alignment) if para.alignment else None
                    }
                    structure_info['paragraphs'].append(para_info)
                    structure_info['styles'].add(para.style.name if para.style else 'Normal')
            
            # Also get simple text extraction as backup
            simple_text = docx2txt.process(file_path)
            
            return {
                'success': True,
                'text': simple_text if simple_text.strip() else '\n'.join(paragraphs),
                'structure': structure_info,
                'metadata': {
                    'total_paragraphs': len(paragraphs),
                    'file_type': 'docx'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse DOCX: {str(e)}'
            }
    
    @staticmethod
    def _parse_txt(file_path: str) -> Dict[str, any]:
        """Parse plain text file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            lines = content.split('\n')
            
            return {
                'success': True,
                'text': content,
                'structure': {
                    'lines': lines,
                    'total_lines': len(lines)
                },
                'metadata': {
                    'total_lines': len(lines),
                    'file_type': 'txt'
                }
            }
            
        except UnicodeDecodeError:
            # Try different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                
                return {
                    'success': True,
                    'text': content,
                    'structure': {'lines': content.split('\n')},
                    'metadata': {'file_type': 'txt', 'encoding': 'latin-1'}
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to parse TXT file: {str(e)}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse TXT file: {str(e)}'
            }
    
    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, str]:
        """Validate if file exists and is readable"""
        
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        if not os.path.isfile(file_path):
            return False, "Path is not a file"
        
        file_extension = os.path.splitext(file_path)[1].lower()
        allowed_extensions = ['.pdf', '.docx', '.txt']
        
        if file_extension not in allowed_extensions:
            return False, f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        
        try:
            with open(file_path, 'rb') as f:
                f.read(1)  # Try to read first byte
        except Exception as e:
            return False, f"Cannot read file: {str(e)}"
        
        return True, "File is valid"