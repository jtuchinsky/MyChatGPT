"""Unit tests for the document loading module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import requests

from src.injestion.load_document import (
    FileSystemInterface,
    DefaultFileSystem,
    DocumentDownloader,
    HTTPDocumentDownloader,
    DocumentLoadService,
    DocumentRepository,
)


class TestDefaultFileSystem:
    """Tests for DefaultFileSystem class."""

    def test_exists_returns_true_when_file_exists(self, tmp_path):
        """Test that exists returns True for existing files."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")

        fs = DefaultFileSystem()
        assert fs.exists(file_path) is True

    def test_exists_returns_false_when_file_does_not_exist(self, tmp_path):
        """Test that exists returns False for non-existent files."""
        file_path = tmp_path / "nonexistent.txt"

        fs = DefaultFileSystem()
        assert fs.exists(file_path) is False

    def test_write_bytes_creates_file_with_content(self, tmp_path):
        """Test that write_bytes creates a file with the correct content."""
        file_path = tmp_path / "test.bin"
        content = b"test binary content"

        fs = DefaultFileSystem()
        fs.write_bytes(file_path, content)

        assert file_path.exists()
        assert file_path.read_bytes() == content

    def test_create_directory_creates_new_directory(self, tmp_path):
        """Test that create_directory creates a new directory."""
        dir_path = tmp_path / "new_dir"

        fs = DefaultFileSystem()
        fs.create_directory(dir_path)

        assert dir_path.exists()
        assert dir_path.is_dir()

    def test_create_directory_creates_nested_directories(self, tmp_path):
        """Test that create_directory creates nested directories."""
        dir_path = tmp_path / "level1" / "level2" / "level3"

        fs = DefaultFileSystem()
        fs.create_directory(dir_path)

        assert dir_path.exists()
        assert dir_path.is_dir()

    def test_create_directory_does_not_fail_if_directory_exists(self, tmp_path):
        """Test that create_directory doesn't fail for existing directories."""
        dir_path = tmp_path / "existing_dir"
        dir_path.mkdir()

        fs = DefaultFileSystem()
        fs.create_directory(dir_path)  # Should not raise

        assert dir_path.exists()


class TestHTTPDocumentDownloader:
    """Tests for HTTPDocumentDownloader class."""

    def test_init_sets_default_timeout_and_chunk_size(self):
        """Test that initialization sets default values."""
        downloader = HTTPDocumentDownloader()

        assert downloader.timeout == 30
        assert downloader.chunk_size == 8192

    def test_init_accepts_custom_timeout_and_chunk_size(self):
        """Test that initialization accepts custom values."""
        downloader = HTTPDocumentDownloader(timeout=60, chunk_size=16384)

        assert downloader.timeout == 60
        assert downloader.chunk_size == 16384

    @patch("src.injestion.load_document.requests.get")
    def test_download_success(self, mock_get, tmp_path):
        """Test successful download of a document."""
        # Setup
        url = "https://example.com/document.pdf"
        destination = tmp_path / "documents" / "document.pdf"
        content = b"PDF content here"

        mock_response = Mock()
        mock_response.content = content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Execute
        downloader = HTTPDocumentDownloader()
        downloader.download(url, destination)

        # Verify
        mock_get.assert_called_once_with(url, stream=True, timeout=30)
        mock_response.raise_for_status.assert_called_once()
        assert destination.exists()
        assert destination.read_bytes() == content

    @patch("src.injestion.load_document.requests.get")
    def test_download_creates_parent_directory(self, mock_get, tmp_path):
        """Test that download creates parent directories."""
        # Setup
        url = "https://example.com/document.pdf"
        destination = tmp_path / "level1" / "level2" / "document.pdf"
        content = b"test content"

        mock_response = Mock()
        mock_response.content = content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Execute
        downloader = HTTPDocumentDownloader()
        downloader.download(url, destination)

        # Verify
        assert destination.parent.exists()
        assert destination.exists()

    @patch("src.injestion.load_document.requests.get")
    def test_download_raises_http_error_on_failed_request(self, mock_get, tmp_path):
        """Test that download raises HTTPError on failed requests."""
        # Setup
        url = "https://example.com/nonexistent.pdf"
        destination = tmp_path / "document.pdf"

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        # Execute & Verify
        downloader = HTTPDocumentDownloader()
        with pytest.raises(requests.HTTPError):
            downloader.download(url, destination)

    @patch("src.injestion.load_document.requests.get")
    def test_download_uses_custom_timeout(self, mock_get, tmp_path):
        """Test that download uses custom timeout value."""
        # Setup
        url = "https://example.com/document.pdf"
        destination = tmp_path / "document.pdf"
        custom_timeout = 60

        mock_response = Mock()
        mock_response.content = b"content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Execute
        downloader = HTTPDocumentDownloader(timeout=custom_timeout)
        downloader.download(url, destination)

        # Verify
        mock_get.assert_called_once_with(url, stream=True, timeout=custom_timeout)

    def test_is_instance_of_document_downloader(self):
        """Test that HTTPDocumentDownloader is a DocumentDownloader."""
        downloader = HTTPDocumentDownloader()
        assert isinstance(downloader, DocumentDownloader)


class TestDocumentLoadService:
    """Tests for DocumentLoadService class."""

    def test_init_with_default_file_system(self):
        """Test initialization with default file system."""
        downloader = Mock(spec=DocumentDownloader)
        service = DocumentLoadService(downloader)

        assert service.downloader is downloader
        assert isinstance(service.file_system, DefaultFileSystem)

    def test_init_with_custom_file_system(self):
        """Test initialization with custom file system."""
        downloader = Mock(spec=DocumentDownloader)
        file_system = Mock(spec=FileSystemInterface)
        service = DocumentLoadService(downloader, file_system)

        assert service.downloader is downloader
        assert service.file_system is file_system

    def test_load_document_downloads_when_file_does_not_exist(self):
        """Test that load_document downloads when file doesn't exist."""
        # Setup
        downloader = Mock(spec=DocumentDownloader)
        file_system = Mock(spec=FileSystemInterface)
        file_system.exists.return_value = False

        service = DocumentLoadService(downloader, file_system)

        url = "https://example.com/doc.pdf"
        destination = Path("/path/to/doc.pdf")

        # Execute
        result = service.load_document(url, destination)

        # Verify
        assert result is True
        file_system.exists.assert_called_once_with(destination)
        file_system.create_directory.assert_called_once_with(destination.parent)
        downloader.download.assert_called_once_with(url, destination)

    def test_load_document_skips_when_file_exists_and_skip_enabled(self):
        """Test that load_document skips download when file exists."""
        # Setup
        downloader = Mock(spec=DocumentDownloader)
        file_system = Mock(spec=FileSystemInterface)
        file_system.exists.return_value = True

        service = DocumentLoadService(downloader, file_system)

        url = "https://example.com/doc.pdf"
        destination = Path("/path/to/doc.pdf")

        # Execute
        result = service.load_document(url, destination, skip_if_exists=True)

        # Verify
        assert result is False
        file_system.exists.assert_called_once_with(destination)
        file_system.create_directory.assert_not_called()
        downloader.download.assert_not_called()

    def test_load_document_downloads_when_file_exists_and_skip_disabled(self):
        """Test that load_document downloads even when file exists if skip is disabled."""
        # Setup
        downloader = Mock(spec=DocumentDownloader)
        file_system = Mock(spec=FileSystemInterface)
        file_system.exists.return_value = True

        service = DocumentLoadService(downloader, file_system)

        url = "https://example.com/doc.pdf"
        destination = Path("/path/to/doc.pdf")

        # Execute
        result = service.load_document(url, destination, skip_if_exists=False)

        # Verify
        assert result is True
        file_system.exists.assert_not_called()
        file_system.create_directory.assert_called_once_with(destination.parent)
        downloader.download.assert_called_once_with(url, destination)

    def test_load_document_propagates_download_errors(self):
        """Test that load_document propagates errors from downloader."""
        # Setup
        downloader = Mock(spec=DocumentDownloader)
        downloader.download.side_effect = requests.HTTPError("404")
        file_system = Mock(spec=FileSystemInterface)
        file_system.exists.return_value = False

        service = DocumentLoadService(downloader, file_system)

        url = "https://example.com/doc.pdf"
        destination = Path("/path/to/doc.pdf")

        # Execute & Verify
        with pytest.raises(requests.HTTPError):
            service.load_document(url, destination)


class TestDocumentRepository:
    """Tests for DocumentRepository class."""

    def test_init_sets_base_directory(self):
        """Test that initialization sets the base directory."""
        base_dir = Path("/documents")
        repo = DocumentRepository(base_dir)

        assert repo.base_directory == base_dir

    def test_get_document_path_returns_correct_path(self):
        """Test that get_document_path returns the correct full path."""
        base_dir = Path("/documents")
        repo = DocumentRepository(base_dir)

        filename = "test.pdf"
        result = repo.get_document_path(filename)

        assert result == Path("/documents/test.pdf")

    def test_get_document_path_with_different_filenames(self):
        """Test get_document_path with various filenames."""
        base_dir = Path("/documents")
        repo = DocumentRepository(base_dir)

        test_cases = [
            ("simple.pdf", Path("/documents/simple.pdf")),
            ("with spaces.pdf", Path("/documents/with spaces.pdf")),
            ("nested/path.pdf", Path("/documents/nested/path.pdf")),
        ]

        for filename, expected in test_cases:
            result = repo.get_document_path(filename)
            assert result == expected

    def test_ensure_directory_exists_creates_directory(self, tmp_path):
        """Test that ensure_directory_exists creates the base directory."""
        base_dir = tmp_path / "new_documents"
        repo = DocumentRepository(base_dir)

        repo.ensure_directory_exists()

        assert base_dir.exists()
        assert base_dir.is_dir()

    def test_ensure_directory_exists_creates_nested_directories(self, tmp_path):
        """Test that ensure_directory_exists creates nested directories."""
        base_dir = tmp_path / "level1" / "level2" / "documents"
        repo = DocumentRepository(base_dir)

        repo.ensure_directory_exists()

        assert base_dir.exists()
        assert base_dir.is_dir()

    def test_ensure_directory_exists_does_not_fail_if_exists(self, tmp_path):
        """Test that ensure_directory_exists doesn't fail for existing directories."""
        base_dir = tmp_path / "existing"
        base_dir.mkdir()
        repo = DocumentRepository(base_dir)

        repo.ensure_directory_exists()  # Should not raise

        assert base_dir.exists()


class TestIntegration:
    """Integration tests for the complete document loading workflow."""

    @patch("src.injestion.load_document.requests.get")
    def test_complete_workflow_new_download(self, mock_get, tmp_path):
        """Test complete workflow for downloading a new document."""
        # Setup
        base_dir = tmp_path / "documents"
        url = "https://example.com/test.pdf"
        filename = "test.pdf"
        content = b"PDF content"

        mock_response = Mock()
        mock_response.content = content
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create components
        repository = DocumentRepository(base_dir)
        repository.ensure_directory_exists()

        downloader = HTTPDocumentDownloader()
        service = DocumentLoadService(downloader)

        destination = repository.get_document_path(filename)

        # Execute
        result = service.load_document(url, destination)

        # Verify
        assert result is True
        assert destination.exists()
        assert destination.read_bytes() == content

    @patch("src.injestion.load_document.requests.get")
    def test_complete_workflow_skip_existing(self, mock_get, tmp_path):
        """Test complete workflow skipping existing document."""
        # Setup
        base_dir = tmp_path / "documents"
        base_dir.mkdir()
        url = "https://example.com/test.pdf"
        filename = "test.pdf"
        existing_content = b"Existing content"

        destination = base_dir / filename
        destination.write_bytes(existing_content)

        # Create components
        repository = DocumentRepository(base_dir)
        downloader = HTTPDocumentDownloader()
        service = DocumentLoadService(downloader)

        destination = repository.get_document_path(filename)

        # Execute
        result = service.load_document(url, destination, skip_if_exists=True)

        # Verify
        assert result is False
        assert destination.read_bytes() == existing_content
        mock_get.assert_not_called()

    def test_mock_file_system_allows_testing_without_disk_io(self):
        """Test that using a mock file system allows testing without disk I/O."""
        # Setup
        mock_downloader = Mock(spec=DocumentDownloader)
        mock_file_system = Mock(spec=FileSystemInterface)
        mock_file_system.exists.return_value = False

        service = DocumentLoadService(mock_downloader, mock_file_system)

        url = "https://example.com/doc.pdf"
        destination = Path("/virtual/path/doc.pdf")

        # Execute
        result = service.load_document(url, destination)

        # Verify - all operations go through mocks, no actual disk I/O
        assert result is True
        mock_file_system.exists.assert_called_once()
        mock_file_system.create_directory.assert_called_once()
        mock_downloader.download.assert_called_once()