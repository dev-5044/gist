import configparser
import time

from selenium import webdriver

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from custom_logger import logger

config = configparser.ConfigParser()
config.read('config.ini')
driver_path = config.get("Driver","PATH")


class Browser:
    def __init__(self, gui=False, proxy=None, profile=None):
        options = Options()
        if proxy is not None:
            options.add_argument('--proxy-server=http://%s' % proxy)
        if profile is not None:
            options.add_argument(f"--user-data-dir={profile}")
        if not gui:
            options.headless = True
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
        self.browser = webdriver.Chrome(executable_path=driver_path,
                                        options=options)
        self.browser.set_window_size(1920, 1080)
        logger.info('browser is created')

    def _wait_elems(self, xpath, timeout=5):
        return WebDriverWait(self.browser, timeout).until(ec.presence_of_all_elements_located((By.XPATH, xpath)))

    def get_screenshot(self, name):
        self.browser.get_screenshot_as_file(f'./screenshots/{name}.png')

    def interaction_with(self, xpath, timeout=10, clickable=False, scroll=False, click=False, text=None):
        """ Функция взаимодействия с элементомами. Возвращает запрошенный элемент """
        # Дожидаемся появления элемента на странице
        elems = self._wait_elems(xpath, timeout)

        # Проверяем сколько элементов обнаружено
        if len(elems) > 1:
            # Если найдена группа элементов, то возвращаем список элементов
            return elems
        else:
            # Иначе - начинаем взаимодействие
            elem: object = elems[0]

        if clickable:
            # Дожидаемся кликабельности элемента
            WebDriverWait(self.browser, timeout).until(ec.element_to_be_clickable((By.XPATH, xpath)))

        if scroll:
            # Скроллим элемент в пределы видимости:
            elem.location_once_scrolled_into_view

        if click:
            # Нажимаем на элемент
            self.browser.execute_script("(arguments[0]).click();", elem)
        if text is not None:
            # Вводим текст
            elem.clear()
            elem.send_keys(text)
            elem.submit()
            print(text, 'from browser')

        return elem
