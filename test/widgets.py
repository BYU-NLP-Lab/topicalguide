
global driver

def infect(driver_):
    global driver
    driver = driver_

class Widget:
    selector = None

    def __init__(self, driver):
        self.driver = driver

    def setup_class(self):
        if self.selector is None:
            raise Exception('You need to assign me a selector: %s' % self)
        self.node = driver(self.selector)

class WordInContext(Widget):
    '''The word in context tab should work'''

    def test_one(self):
        '''There should be at least one loaded entry'''
        rows = self.node.findall('tbody tr')
        assert len(rows)
        row = rows[0]
        assert row.get_attribute('word') == row.find('td.word a').text


