import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from core.errors import AppError
from scripts import setup_max
from services import max_bot


class MaxSetupTests(unittest.TestCase):
    def settings(self, token='', username=''):
        return SimpleNamespace(max_bot_token=token, max_bot_username=username, max_ca_bundle=None)

    def test_hidden_input_and_bot_link_without_host(self):
        settings = self.settings()
        output = io.StringIO()
        with patch.object(setup_max, 'getpass', return_value='private-test-token') as prompt, patch.object(setup_max, 'api_call', return_value={'is_bot': True, 'username': 'school_bot'}) as request, redirect_stdout(output):
            setup_max.check_token(settings)
        prompt.assert_called_once()
        request.assert_called_once_with('/me')
        self.assertIn('https://max.ru/school_bot', output.getvalue())
        self.assertNotIn('private-test-token', output.getvalue())

    def test_saved_token_does_not_prompt_and_flags_wrong_username(self):
        output = io.StringIO()
        with patch.object(setup_max, 'getpass') as prompt, patch.object(setup_max, 'api_call', return_value={'is_bot': True, 'username': 'real_bot'}), redirect_stdout(output):
            setup_max.check_token(self.settings('saved-secret', 'wrong_bot'))
        prompt.assert_not_called()
        self.assertIn('MAX_BOT_USERNAME=real_bot', output.getvalue())
        self.assertIn('другое имя', output.getvalue())
        self.assertNotIn('saved-secret', output.getvalue())

    def test_link_is_not_accepted_as_token(self):
        with patch.object(setup_max, 'getpass', return_value='https://enigma.vkteam.ru/v/example'), patch.object(setup_max, 'api_call') as request:
            with self.assertRaises(SystemExit):
                setup_max.check_token(self.settings())
        request.assert_not_called()

    def test_invalid_bot_identity(self):
        for response in ({'is_bot': False, 'username': 'person'}, {'is_bot': True, 'username': None}, {'is_bot': True, 'username': '../bad'}, []):
            with self.subTest(response=response), patch.object(setup_max, 'api_call', return_value=response):
                with self.assertRaises(SystemExit):
                    setup_max.check_token(self.settings('secret'))

    def test_api_errors_are_clear_and_do_not_echo_response(self):
        errors = [HTTPError('https://example.test', code, 'secret-response', {}, None) for code in (401, 403, 429, 500)]
        errors += [URLError('secret-response'), ValueError('secret-response')]
        for error in errors:
            with self.subTest(error=type(error).__name__), patch.object(max_bot, 'get_settings', return_value=self.settings('secret-token')), patch.object(max_bot, 'urlopen', side_effect=error):
                with self.assertRaises(AppError) as raised:
                    max_bot.api_call('/me')
                self.assertNotIn('secret-response', raised.exception.detail)
                self.assertNotIn('secret-token', raised.exception.detail)
                if isinstance(error, HTTPError):
                    self.assertIn(str(error.code), raised.exception.detail)


if __name__ == '__main__':
    unittest.main()
