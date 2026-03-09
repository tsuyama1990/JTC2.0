
with open("tests/unit/test_file_service.py") as f:
    content = f.read()

diff = """<<<<<<< SEARCH
    @patch("src.core.services.file_service.FileService._validate_path")
    def test_save_text_async_os_error(
=======
    @patch("src.core.services.file_service.FileService._validate_path")
    def test_save_text_async_large_file(
        self, mock_validate: MagicMock, file_service: FileService
    ) -> None:
        \"\"\"Verify handling of large string payloads.\"\"\"
        with (
            patch("tempfile.mkstemp") as mock_mkstemp,
            patch("os.fdopen") as mock_fdopen,
            patch("os.replace") as mock_replace,
        ):
            mock_path = MagicMock()
            mock_path.__str__.return_value = "large.md" # type: ignore[attr-defined]
            mock_validate.return_value = mock_path
            mock_path.parent = MagicMock()
            mock_mkstemp.return_value = (1, "temp.md")
            mock_file = MagicMock()
            mock_fdopen.return_value.__enter__.return_value = mock_file

            large_content = "A" * (1024 * 1024 * 10)  # 10 MB string
            file_service.save_text_async(large_content, "large.md")
            file_service._executor.shutdown(wait=True)

            mock_file.write.assert_called_with(large_content)
            mock_replace.assert_called_once()

    @patch("src.core.services.file_service.FileService._validate_path")
    def test_save_text_async_os_error(
>>>>>>> REPLACE"""

with open("patch_file_service_tests.patch", "w") as f:
    f.write(diff)
