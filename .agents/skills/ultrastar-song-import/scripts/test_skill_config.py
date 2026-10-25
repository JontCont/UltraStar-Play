"""Tests for skill_config. Uses temporary files only and never reads the real .env."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import skill_config as config
from chart_core import ChartError

KEYS = (config.LIBRARY_KEY, config.WORK_ROOT_KEY)


class EnvTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        patcher = mock.patch.dict(os.environ)
        patcher.start()
        self.addCleanup(patcher.stop)
        for key in KEYS:
            os.environ.pop(key, None)


class ParseEnvTests(unittest.TestCase):
    def test_skips_comments_and_blank_lines(self):
        self.assertEqual(config.parse_env("# note\n\nA=1\n"), {"A": "1"})

    def test_strips_matching_quotes_only(self):
        values = config.parse_env('A="x y"\nB=\'z\'\nC="unclosed\n')
        self.assertEqual(values, {"A": "x y", "B": "z", "C": '"unclosed'})

    def test_keeps_equals_and_spaces_in_value(self):
        values = config.parse_env("NAME = C:\\Music\\UltraStar Play=x\n")
        self.assertEqual(values, {"NAME": "C:\\Music\\UltraStar Play=x"})


class ReadEnvFileTests(EnvTestCase):
    def test_missing_file_gives_no_values(self):
        self.assertEqual(config.read_env_file(self.root / "absent.env"), {})

    def test_reads_utf8_with_bom(self):
        path = self.root / ".env"
        path.write_bytes("\ufeff{}=C:\\Music\\UltraStar Play\n".format(config.LIBRARY_KEY).encode("utf-8"))
        self.assertEqual(config.read_env_file(path), {config.LIBRARY_KEY: "C:\\Music\\UltraStar Play"})


class SettingTests(EnvTestCase):
    def test_process_environment_beats_file(self):
        os.environ[config.LIBRARY_KEY] = "C:\\from-env"
        self.assertEqual(config.setting(config.LIBRARY_KEY, {config.LIBRARY_KEY: "C:\\from-file"}),
                         "C:\\from-env")

    def test_file_used_when_environment_missing(self):
        self.assertEqual(config.setting(config.LIBRARY_KEY, {config.LIBRARY_KEY: "C:\\from-file"}),
                         "C:\\from-file")

    def test_absent_setting_is_none(self):
        self.assertIsNone(config.setting(config.LIBRARY_KEY, {}))

    def test_references_are_expanded(self):
        os.environ["ULTRASTAR_TEST_ROOT"] = "C:\\base"
        self.assertEqual(config.setting(config.LIBRARY_KEY, {config.LIBRARY_KEY: "$ULTRASTAR_TEST_ROOT\\Music"}),
                         "C:\\base\\Music")

    def test_unset_percent_reference_is_an_error(self):
        with self.assertRaisesRegex(ChartError, "unset variable"):
            config.setting(config.LIBRARY_KEY, {config.LIBRARY_KEY: "%ULTRASTAR_TEST_UNSET_VARIABLE%\\x"})


class LibraryFolderTests(EnvTestCase):
    def test_flag_beats_file(self):
        flag_dir = self.root / "flag"
        file_dir = self.root / "file"
        flag_dir.mkdir()
        file_dir.mkdir()
        self.assertEqual(config.library_folder(str(flag_dir), {config.LIBRARY_KEY: str(file_dir)}), flag_dir)

    def test_file_used_without_flag(self):
        library = self.root / "library"
        library.mkdir()
        self.assertEqual(config.library_folder(None, {config.LIBRARY_KEY: str(library)}), library)

    def test_missing_setting_is_reported(self):
        with self.assertRaisesRegex(ChartError, "No song library given"):
            config.library_folder(None, {})

    def test_folder_must_exist(self):
        with self.assertRaisesRegex(ChartError, "not found"):
            config.library_folder(None, {config.LIBRARY_KEY: str(self.root / "missing")})
        self.assertFalse((self.root / "missing").exists())


class WorkFolderTests(EnvTestCase):
    def test_file_value_is_used(self):
        self.assertEqual(config.work_root({config.WORK_ROOT_KEY: str(self.root / "work")}), self.root / "work")

    @unittest.skipUnless(os.name == "nt", "the default uses %LOCALAPPDATA% on Windows")
    def test_default_is_under_local_appdata(self):
        os.environ["LOCALAPPDATA"] = str(self.root / "local")
        self.assertEqual(config.work_root({}), self.root / "local" / "UltraStarSongImport")

    def test_default_work_folder_is_named_after_artist_and_title(self):
        folder = config.default_work_folder("Artist", "Title", {config.WORK_ROOT_KEY: str(self.root)})
        self.assertEqual(folder, self.root / "Artist-Title")

    def test_default_work_folder_replaces_unsafe_characters(self):
        folder = config.default_work_folder("A/B", "C:D", {config.WORK_ROOT_KEY: str(self.root)})
        self.assertEqual(folder, self.root / "A_B-C_D")


class ExampleFileTests(unittest.TestCase):
    def test_example_lists_every_key(self):
        text = (config.SKILL_DIR / ".env.example").read_text(encoding="utf-8")
        self.assertEqual(set(config.parse_env(text)), set(KEYS))


if __name__ == "__main__":
    unittest.main()
