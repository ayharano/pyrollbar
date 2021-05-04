import copy
import sys

try:
    from unittest import mock
except ImportError:
    import mock

import unittest2

import rollbar
from rollbar.test import BaseTest

ALLOWED_PYTHON_VERSION = sys.version_info >= (3, 6)


@unittest2.skipUnless(ALLOWED_PYTHON_VERSION, 'Async support requires Python3.6+')
class AsyncLibTest(BaseTest):
    default_settings = copy.deepcopy(rollbar.SETTINGS)

    def setUp(self):
        self.access_token = 'aaaabbbbccccddddeeeeffff00001111'
        rollbar.SETTINGS = copy.deepcopy(self.default_settings)
        rollbar._initialized = False
        rollbar.init(self.access_token, handler='async')

    @mock.patch('rollbar.send_payload')
    def test_report_exception(self, send_payload):
        from rollbar.lib._async import report_exc_info, run

        def _raise():
            try:
                raise Exception('foo')
            except:
                return run(report_exc_info())

        uuid = _raise()

        send_payload.assert_called_once()

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['uuid'], uuid)
        self.assertEqual(payload['access_token'], self.access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('trace', payload['data']['body'])
        self.assertNotIn('trace_chain', payload['data']['body'])
        self.assertIn('exception', payload['data']['body']['trace'])
        self.assertEqual(
            payload['data']['body']['trace']['exception']['message'], 'foo'
        )
        self.assertEqual(
            payload['data']['body']['trace']['exception']['class'], 'Exception'
        )

        self.assertNotIn('argspec', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('varargspec', payload['data']['body']['trace']['frames'][-1])
        self.assertNotIn('keywordspec', payload['data']['body']['trace']['frames'][-1])
        self.assertIn('locals', payload['data']['body']['trace']['frames'][-1])

    @mock.patch('rollbar.send_payload')
    def test_report_messsage(self, send_payload):
        from rollbar.lib._async import report_message, run

        uuid = run(report_message('foo'))

        def r(f):
            x

        send_payload.assert_called_once()

        payload = send_payload.call_args[0][0]

        self.assertEqual(payload['data']['uuid'], uuid)
        self.assertEqual(payload['access_token'], self.access_token)
        self.assertIn('body', payload['data'])
        self.assertIn('message', payload['data']['body'])
        self.assertIn('body', payload['data']['body']['message'])
        self.assertEqual(payload['data']['body']['message']['body'], 'foo')

    @mock.patch('rollbar.report_exc_info')
    def test_should_run_rollbar_report_exc_info(self, rollbar_report_exc_info):
        from rollbar.lib._async import report_exc_info, run

        try:
            raise Exception()
        except Exception:
            run(
                report_exc_info(
                    'exc_info',
                    'request',
                    'extra_data',
                    'payload_data',
                    'level_data',
                    foo='bar',
                )
            )

        rollbar_report_exc_info.assert_called_once_with(
            'exc_info', 'request', 'extra_data', 'payload_data', 'level_data', foo='bar'
        )

    @mock.patch('rollbar.report_message')
    def test_should_run_rollbar_report_message(self, rollbar_report_message):
        from rollbar.lib._async import report_message, run

        run(report_message('message', 'level', 'request', 'extra_data', 'payload_data'))

        rollbar_report_message.assert_called_once_with(
            'message', 'level', 'request', 'extra_data', 'payload_data'
        )

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_async')
    def test_report_exc_info_should_use_async_handler_regardless_of_settings(
        self, mock__send_payload_async, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        rollbar.SETTINGS['handler'] = 'default'
        self.assertEqual(rollbar.SETTINGS['handler'], 'default')

        run(report_exc_info())

        self.assertEqual(rollbar.SETTINGS['handler'], 'default')
        mock__send_payload_async.assert_called_once()
        mock_log.assert_called_once_with(
            'Running coroutines requires async compatible handler. Switching to default async handler.'
        )

    @mock.patch('logging.Logger.warning')
    @mock.patch('rollbar._send_payload_async')
    def test_report_message_should_use_async_handler_regardless_of_settings(
        self, mock__send_payload_async, mock_log
    ):
        import rollbar
        from rollbar.lib._async import report_message, run

        rollbar.SETTINGS['handler'] = 'default'
        self.assertEqual(rollbar.SETTINGS['handler'], 'default')

        run(report_message('foo'))

        self.assertEqual(rollbar.SETTINGS['handler'], 'default')
        mock__send_payload_async.assert_called_once()
        mock_log.assert_called_once_with(
            'Running coroutines requires async compatible handler. Switching to default async handler.'
        )

    @mock.patch('rollbar._send_payload_async')
    def test_report_exc_info_should_allow_async_handler(self, mock__send_payload_async):
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        rollbar.SETTINGS['handler'] = 'async'
        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

        run(report_exc_info())

        self.assertEqual(rollbar.SETTINGS['handler'], 'async')
        mock__send_payload_async.assert_called_once()

    @mock.patch('rollbar._send_payload_async')
    def test_report_message_should_allow_async_handler(self, mock__send_payload_async):
        import rollbar
        from rollbar.lib._async import report_message, run

        rollbar.SETTINGS['handler'] = 'async'
        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

        run(report_message('foo'))

        self.assertEqual(rollbar.SETTINGS['handler'], 'async')
        mock__send_payload_async.assert_called_once()

    @mock.patch('rollbar._send_payload_httpx')
    def test_report_exc_info_should_allow_httpx_handler(self, mock__send_payload_httpx):
        import rollbar
        from rollbar.lib._async import report_exc_info, run

        rollbar.SETTINGS['handler'] = 'httpx'
        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')

        run(report_exc_info())

        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')
        mock__send_payload_httpx.assert_called_once()

    @mock.patch('rollbar._send_payload_httpx')
    def test_report_message_should_allow_httpx_handler(self, mock__send_payload_httpx):
        import rollbar
        from rollbar.lib._async import report_message, run

        rollbar.SETTINGS['handler'] = 'httpx'
        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')

        run(report_message('foo', 'error'))

        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')
        mock__send_payload_httpx.assert_called_once()

    @mock.patch('logging.Logger.warning')
    def test_ctx_manager_should_temporary_set_async_handler(self, mock_log):
        import rollbar
        from rollbar.lib._async import async_handler

        rollbar.SETTINGS['handler'] = 'threading'
        self.assertEqual(rollbar.SETTINGS['handler'], 'threading')

        with async_handler() as handler:
            self.assertEqual(handler, 'async')
            self.assertEqual(rollbar.SETTINGS['handler'], handler)
            mock_log.assert_called_once_with(
                'Running coroutines requires async compatible handler.'
                ' Switching to default async handler.'
            )

        self.assertEqual(rollbar.SETTINGS['handler'], 'threading')

    def test_ctx_manager_should_not_substitute_async_handler(self):
        import rollbar
        from rollbar.lib._async import async_handler

        rollbar.SETTINGS['handler'] = 'async'
        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

        with async_handler() as handler:
            self.assertEqual(handler, 'async')
            self.assertEqual(rollbar.SETTINGS['handler'], handler)

        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

    def test_ctx_manager_should_not_substitute_httpx_handler(self):
        import rollbar
        from rollbar.lib._async import async_handler

        rollbar.SETTINGS['handler'] = 'httpx'
        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')

        with async_handler() as handler:
            self.assertEqual(handler, 'httpx')
            self.assertEqual(rollbar.SETTINGS['handler'], handler)

        self.assertEqual(rollbar.SETTINGS['handler'], 'httpx')

    @mock.patch('rollbar.lib._async.report_exc_info')
    def test_should_try_report_with_async_handler(self, async_report_exc_info):
        import rollbar
        from rollbar.lib._async import run, try_report

        self.assertEqual(rollbar.SETTINGS['handler'], 'async')

        run(try_report())

        async_report_exc_info.assert_called_once()

    @mock.patch('rollbar.lib._async.report_exc_info')
    def test_should_not_try_report_with_async_handler_if_non_async_handler(
        self, async_report_exc_info
    ):
        import rollbar
        from rollbar.lib._async import RollbarAsyncError, run, try_report

        rollbar.SETTINGS['handler'] = 'threading'
        self.assertEqual(rollbar.SETTINGS['handler'], 'threading')

        with self.assertRaises(RollbarAsyncError):
            run(try_report())

        async_report_exc_info.assert_not_called()

    @mock.patch('asyncio.ensure_future')
    @mock.patch('asyncio.create_task')
    def test_should_schedule_task_in_event_loop(self, create_task, ensure_future):
        from rollbar.lib._async import call_later, coroutine

        try:
            coro = coroutine()
            call_later(coro)

            if sys.version_info >= (3, 7):
                create_task.assert_called_once_with(coro)
                ensure_future.assert_not_called()
            else:
                create_task.assert_not_called()
                ensure_future.assert_called_once_with(coro)
        finally:
            # make sure the coroutine is closed to avoid RuntimeWarning by calling
            # coroutine without awaiting it later
            coro.close()
