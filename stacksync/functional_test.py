import unittest
from selenium import webdriver
import uuid
from selenium.webdriver.common.keys import Keys


class StacksyncWebTests(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()
        self.base_url = "http://127.0.0.1:8000"

    def tearDown(self):
        self.browser.quit()

    def test_stacksync_webapp_starts(self):
        self.browser.get('http://localhost:8000')
        self.assertEquals('Stack Sync', self.browser.title)

    def login_stacksync(self):
        self.browser.get(self.base_url + "/log_in/")
        self.browser.find_element_by_id("id_username").clear()
        self.browser.find_element_by_id("id_username").send_keys("john.doe@yahoo.com")
        self.browser.find_element_by_id("id_password").clear()
        self.browser.find_element_by_id("id_password").send_keys("testpass")
        self.browser.find_element_by_xpath("//button[@type='submit']").click()

    def test_login(self):
        self.login_stacksync()

        self.assertEquals('Proyecto - Bienvenido', self.browser.title)

    def test_create_a_new_folder(self):
        self.login_stacksync()
        self.browser.find_element_by_id("folder").click()
        prompt = self.browser.switch_to.alert

        name_of_folder = str(uuid.uuid4())

        prompt.send_keys(name_of_folder)
        # prompt.send_keys(Keys.ENTER)
        prompt.accept()

        # self.browser.get(self.base_url)
        table = self.browser.find_element_by_id('myTable')
        rows = table.find_elements_by_tag_name('tr')
        self.assertTrue(
            any(name_of_folder.lower() in row.text.lower() for row in rows)
        )


