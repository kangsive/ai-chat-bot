import os
import uuid
import shutil
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, List

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


class FileStorageService:
    """Service for handling file storage operations."""
    
    def __init__(self):
        """Initialize the service and ensure upload directory exists."""
        # Ensure the upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Create year/month subdirectories for better organization
        current_date = datetime.now()
        year_month = f"{current_date.year}/{current_date.month:02d}"
        self.upload_path = os.path.join(settings.UPLOAD_DIR, year_month)
        os.makedirs(self.upload_path, exist_ok=True)
    
    def get_file_extension(self, filename: str) -> str:
        """Get the file extension from the filename."""
        return Path(filename).suffix.lstrip(".").lower()
    
    def is_valid_file(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate if the uploaded file meets the requirements.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset file position
        
        if file_size > settings.MAX_UPLOAD_SIZE:
            return False, f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024} MB"
        
        # Check file extension
        extension = self.get_file_extension(file.filename)
        if extension not in settings.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        
        return True, None
    
    def is_file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the storage."""
        return os.path.exists(file_path)
    
    async def save_file(self, file: UploadFile, message_id: uuid.UUID) -> dict:
        """
        Save an uploaded file to storage.
        
        Args:
            file: The uploaded file
            message_id: The ID of the message this file is attached to
            
        Returns:
            dict: Metadata about the saved file
        """
        # Validate file
        is_valid, error_message = self.is_valid_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Generate a unique filename to prevent collisions
        extension = self.get_file_extension(file.filename)
        unique_filename = f"{message_id}_{uuid.uuid4()}.{extension}"
        file_path = os.path.join(self.upload_path, unique_filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file metadata
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            "filename": file.filename,  # Original filename
            "file_path": file_path,  # Path where file is stored
            "file_type": mime_type or f"application/{extension}",  # MIME type
            "file_size": file_size,  # Size in bytes
        }
    
    def get_file_path(self, file_path: str) -> str:
        """
        Get the full path to a file.
        
        Args:
            file_path: The stored file path
            
        Returns:
            str: The full path to the file
        """
        return file_path
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: The path to the file to delete
            
        Returns:
            bool: True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False


file_storage_service = FileStorageService() 