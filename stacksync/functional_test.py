import unittest
from selenium import webdriver
import uuid
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class StacksyncWebTests(unittest.TestCase):
    """
    You must have a django server running to run this test
    manage runserver 8000 (just run your regular django dev server and then run the tests)
    """
    def setUp(self):
        self.browser = webdriver.Firefox()
        self.base_url = "http://127.0.0.1:8000"

    def tearDown(self):
        self.browser.quit()

    # def test_stacksync_webapp_starts(self):
    #     self.browser.get('http://localhost:8000')
    #     self.assertEquals('Stack Sync', self.browser.title)
    #
    def login_stacksync(self):
        self.browser.get(self.base_url + "/log_in/")
        self.browser.find_element_by_id("id_username").clear()
        self.browser.find_element_by_id("id_username").send_keys("john.doe@yahoo.com")
        self.browser.find_element_by_id("id_password").clear()
        self.browser.find_element_by_id("id_password").send_keys("testpass")
        self.browser.find_element_by_xpath("//button[@type='submit']").click()
    #
    # def test_login(self):
    #     self.login_stacksync()
    #
    #     self.assertEquals('Proyecto - Bienvenido', self.browser.title)

    def create_folder(self):
        self.browser.find_element_by_id("folder").click()
        prompt = self.browser.switch_to.alert
        name_of_folder = str(uuid.uuid4())
        prompt.send_keys(name_of_folder)
        # prompt.send_keys(Keys.ENTER)
        prompt.accept()
        return name_of_folder

    # def test_create_a_new_folder(self):
    #     self.login_stacksync()
    #     name_of_folder = self.create_folder()
    #
    #     table = self.browser.find_element_by_id('myTable')
    #     rows = table.find_elements_by_tag_name('tr')
    #     self.assertTrue(
    #         any(name_of_folder.lower() in row.text.lower() for row in rows)
    #     )

    def find_folder(self, name_of_folder):
        table = self.browser.find_element_by_id('myTable')
        rows = table.find_elements_by_tag_name('tr')
        return [row for row in rows if name_of_folder.lower() in row.text.lower()]


    def open_folder_context_menu(self):
        actions = ActionChains(self.browser)
        element_to_right_click_working = self.browser.find_elements_by_css_selector("#myTable td")
        element_to_right_click_working = element_to_right_click_working[4]
        actions.move_to_element(element_to_right_click_working)
        actions.context_click(element_to_right_click_working)
        actions.perform()

    def test_get_folder_members(self):
        self.login_stacksync()
        # name_of_folder = self.create_folder()
        # element_to_right_click = self.find_folder('469dadef-9647-444d-9aa3-3e595d0e9be8')[0]
        # self.assertIn(name_of_folder, element_to_right_click.text.lower())

        self.open_folder_context_menu()
        hidden_menu_share_option = self.browser.find_element_by_css_selector('#jqContextMenu > ul > li#share').click()
        folder_members=self.browser.find_elements_by_css_selector('#folder-members option')

        self.assertEquals(2, len(folder_members))

    def test_share_a_folder(self):
        self.login_stacksync()

        self.open_folder_context_menu()
        hidden_menu_share_option = self.browser.find_element_by_css_selector('#jqContextMenu > ul > li#share').click()
        folder_members=self.browser.find_elements_by_css_selector('#folder-members option')
        input_text = self.browser.find_elements_by_css_selector("#folder-members + div > input")
