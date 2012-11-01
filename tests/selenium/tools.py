#!/usr/bin/env python

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
import time
import os

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

BASE_DIR = os.path.dirname(__file__)

##  my injection...
def findall(self, css=None, id=None, tag=None, name=None, xpath=None):
    '''This is a convenience function to make finding elements less wordy.
    
    css is the default. now you can do things like:
        driver('#elem')
    '''
    if css:
        return self.find_elements(By.CSS_SELECTOR, css)
    if id:
        return self.find_elements(By.ID, id)
    if tag:
        return self.find_elements(By.TAG_NAME, tag)
    if name:
        return self.find_elements(By.NAME, name)
    if xpath:
        return self.find_elements(By.XPATH, xpath)

def find(self, css=None, id=None, tag=None, name=None, xpath=None):
    '''This is a convenience function to make finding elements less wordy.
    
    css is the default. now you can do things like:
        driver('#elem')
    '''
    if css:
        return self.find_element(By.CSS_SELECTOR, css)
    if id:
        return self.find_element(By.ID, id)
    if tag:
        return self.find_element(By.TAG_NAME, tag)
    if name:
        return self.find_element(By.NAME, name)
    if xpath:
        return self.find_element(By.XPATH, xpath)

def css(self, attr):
    return self.value_of_css_property(attr)

def inject_magic():
    WebDriver.find = find
    WebDriver.findall = findall
    WebDriver.__call__ = find
    WebElement.find = find
    WebElement.findall = findall
    WebElement.__call__ = find
    WebElement.attr = WebElement.get_attribute
    WebElement.css = WebElement.value_of_css_property

def ispageloading(driver):
    return driver.execute_script('return window.loading')
# vim: et sw=4 sts=4
