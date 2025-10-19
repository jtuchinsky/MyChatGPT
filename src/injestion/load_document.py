"""Document loading and downloading module for the ingestion pipeline."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol
import requests


class FileSystemInterface(Protocol):
    """Protocol for file system operations (Dependency Inversion Principle)."""

    def exists(self, path: Path) -> bool:
        """Check if a file exists."""
        ...

    def write_bytes(self, path: Path, content: bytes) -> None:
        """Write bytes to a file."""
        ...

    def create_directory(self, path: Path) -> None:
        """Create a directory if it doesn't exist."""
        ...


class DefaultFileSystem:
    """Default file system implementation."""

    def exists(self, path: Path) -> bool:
        """Check if a file exists."""
        return path.exists()

    def write_bytes(self, path: Path, content: bytes) -> None:
        """Write bytes to a file."""
        path.write_bytes(content)

    def create_directory(self, path: Path) -> None:
        """Create a directory if it doesn't exist."""
        path.mkdir(parents=True, exist_ok=True)


class DocumentDownloader(ABC):
    """Abstract base class for document downloaders (Open/Closed Principle)."""

    @abstractmethod
    def download(self, url: str, destination: Path) -> None:
        """Download a document from a URL to a destination path."""
        ...


class HTTPDocumentDownloader(DocumentDownloader):
    """HTTP-based document downloader (Single Responsibility Principle)."""

    def __init__(self, timeout: int = 30, chunk_size: int = 8192):
        """
        Initialize the HTTP downloader.

        Args:
            timeout: Request timeout in seconds
            chunk_size: Size of chunks for streaming downloads
        """
        self.timeout = timeout
        self.chunk_size = chunk_size

    def download(self, url: str, destination: Path) -> None:
        """
        Download a document from an HTTP URL.

        Args:
            url: The URL to download from
            destination: The local file path to save to

        Raises:
            requests.HTTPError: If the HTTP request fails
            requests.RequestException: For other request-related errors
        """
        response = requests.get(url, stream=True, timeout=self.timeout)
        response.raise_for_status()

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)


class DocumentLoadService:
    """
    Service for managing document downloads (Single Responsibility Principle).

    This class orchestrates the download process while delegating specific
    responsibilities to injected dependencies (Dependency Inversion Principle).
    """

    def __init__(
        self,
        downloader: DocumentDownloader,
        file_system: FileSystemInterface | None = None,
    ):
        """
        Initialize the document load service.

        Args:
            downloader: The downloader implementation to use
            file_system: Optional file system interface (defaults to DefaultFileSystem)
        """
        self.downloader = downloader
        self.file_system = file_system or DefaultFileSystem()

    def load_document(
        self, url: str, destination: Path, skip_if_exists: bool = True
    ) -> bool:
        """
        Load a document from a URL to a local path.

        Args:
            url: The URL to download from
            destination: The local file path to save to
            skip_if_exists: If True, skip download if file already exists

        Returns:
            bool: True if file was downloaded, False if skipped

        Raises:
            requests.HTTPError: If the HTTP request fails
            requests.RequestException: For other request-related errors
        """
        if skip_if_exists and self.file_system.exists(destination):
            return False

        self.file_system.create_directory(destination.parent)
        self.downloader.download(url, destination)
        return True


class DocumentRepository:
    """
    Repository for managing document storage locations (Single Responsibility).

    This class encapsulates the logic for determining where documents
    should be stored based on their source or type.
    """

    def __init__(self, base_directory: Path):
        """
        Initialize the document repository.

        Args:
            base_directory: The base directory for storing documents
        """
        self.base_directory = base_directory

    def get_document_path(self, filename: str) -> Path:
        """
        Get the full path for a document.

        Args:
            filename: The name of the document file

        Returns:
            Path: The full path where the document should be stored
        """
        return self.base_directory / filename

    def ensure_directory_exists(self) -> None:
        """Ensure the base directory exists."""
        self.base_directory.mkdir(parents=True, exist_ok=True)



