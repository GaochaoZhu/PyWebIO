import subprocess
import time

from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio.input import *
from pywebio.utils import to_coroutine, run_as_function


def target():
    template.basic_output()
    template.background_output()

    run_as_function(template.basic_input())
    actions(buttons=['Continue'])
    template.background_input()


async def async_target():
    template.basic_output()
    await template.coro_background_output()

    await to_coroutine(template.basic_input())
    await actions(buttons=['Continue'])
    await template.coro_background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_output(browser)
    time.sleep(1)
    template.test_input(browser)
    time.sleep(1)
    template.save_output(browser, '15.tornado_http_multiple_session_p1.html')

    browser.get('http://localhost:8080/?_pywebio_debug=1&_pywebio_http_pull_interval=400&app=p2')
    template.test_output(browser)
    time.sleep(1)
    template.test_input(browser)

    time.sleep(1)
    template.save_output(browser, '15.tornado_http_multiple_session_p2.html')


def start_test_server():
    pywebio.enable_debug()
    from pywebio.platform.tornado_http import start_server

    start_server({'p1': target, 'p2': async_target}, port=8080, host='127.0.0.1')


if __name__ == '__main__':
    util.run_test(start_test_server, test,
                  address='http://localhost:8080/?_pywebio_debug=1&_pywebio_http_pull_interval=400&app=p1')
