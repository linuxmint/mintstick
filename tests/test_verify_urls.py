"""Checksum URL selection without downloading an ISO or changing a keyring."""
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import Mock, patch

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import gnupg


class VerifyUrlsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = Path(__file__).resolve().parents[1] / 'lib/verify.py'
        with tempfile.TemporaryDirectory() as root:
            original_expanduser = os.path.expanduser

            def expanduser(path):
                if path == '~/.cache/mintstick':
                    return root
                return original_expanduser(path)

            # The script starts its UI when loaded; replace only UI/keyring setup.
            with patch('sys.argv', [str(script), root]), \
                 patch.object(Gtk, 'Builder'), patch.object(Gtk, 'main'), \
                 patch.object(gnupg, 'GPG'), patch('os.path.expanduser', side_effect=expanduser):
                cls.module = runpy.run_path(str(script))
        cls.app_class = cls.module['App']
        cls.mirror = cls.module['MINT_MIRROR']

    def check_urls(self, filename, sums):
        app = self.app_class.__new__(self.app_class)
        app.filename = filename
        entries = {'entry_url_sums': Mock(), 'entry_url_gpg': Mock()}
        app.builder = Mock()
        app.builder.get_object.side_effect = entries.__getitem__
        app.guess_urls()
        entries['entry_url_sums'].set_text.assert_called_once_with(sums)
        entries['entry_url_gpg'].set_text.assert_called_once_with(sums + '.gpg')

    def test_hwe_images(self):
        for desktop in ('cinnamon', 'mate', 'xfce'):
            for kernel in ('6.17', '7.0'):
                with self.subTest(desktop=desktop, kernel=kernel):
                    self.check_urls('linuxmint-22.3-%s-64bit-hwe-%s.iso' % (desktop, kernel),
                                    self.mirror + '/hwe/sha256sum.txt')

    def test_standard_mint(self):
        self.check_urls('linuxmint-22.3-cinnamon-64bit.iso', self.mirror + '/stable/22.3/sha256sum.txt')

    def test_beta(self):
        self.check_urls('linuxmint-22.3-cinnamon-64bit-beta.iso', self.mirror + '/testing/sha256sum.txt')

    def test_lmde(self):
        self.check_urls('lmde-7-cinnamon-64bit.iso', self.mirror + '/debian/sha256sum.txt')

    def test_ubuntu(self):
        self.check_urls('ubuntu-24.04.1-desktop-amd64.iso', 'http://releases.ubuntu.com/24.04/SHA256SUMS')


if __name__ == '__main__':
    unittest.main()
