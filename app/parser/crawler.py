# crawler.py
# James Wang, 11 Jun 2013

"""Crawler that pulls data from hackerschool.com"""

import lxml.html.soupparser
import mechanize


def run_crawler(spider, **kwargs):
    """Runs the crawl. Takes spider to run and keyword arguments needed by
    spider (e.g. username and password). Raises LoginFailedException (through
    spider) if login fails. Otherwise, returns scraped items in a list.

    """
    the_spider = spider(**kwargs)
    the_spider.attempt_login()
    return the_spider.items


class LoginFailedException(Exception):
    """Exception raised if login credentials are rejected."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SuperSpider(object):
    """This is the base spider that tries to connect to the website. Takes
    username and password as arguments. Executes spider.actions(), which must
    be implemented in subclasses and should store scraped results in
    self.items. To begin scraping session, call attempt_login. If login
    credentials are rejected, raises LoginFailedException.

    """
    baseaddress = "https://www.hackerschool.com"
    start_url = baseaddress + "/login"
    target_url = baseaddress + "/private"

    user = ""
    pw = ""
    items = []

    def __init__(self, username, password):
        self.user = username
        self.pw = password

    def attempt_login(self):
        request = mechanize.Request(self.start_url)
        response = mechanize.urlopen(request)

        if response.geturl() == self.target_url:  # already logged in
            return self.action(response)
        else:
            forms = mechanize.ParseResponse(response, backwards_compat=False)
            form = forms[0]  # Grab forms from hackerschool site response
            form['email'] = self.user
            form['password'] = self.pw

            request2 = form.click()
            response2 = mechanize.urlopen(request2)

            if response2.geturl() != self.target_url:  # login failed
                raise LoginFailedException("Credentials rejected.")
            else:
                self.action(response2)

    def action(response):
        raise NotImplementedError("SuperSpider.action must be implemented!")


class BatchSpider(SuperSpider):
    """Spider that scrapes Hacker School website for batches (so the game can
    dynamically update batches as new ones come in. Takes username and password
    as arguments to login to site. Stores list of batches in items attribute.

    """
    def action(self, response):
        html = response.read()
        soup = lxml.html.soupparser.fromstring(html)
        batches = soup.xpath("//ul[@id='batches']/li/ul/@id")
        self.items = get_strs_from_lxml_list(batches)


class HackerSchoolerSpider(SuperSpider):
    """Spider that crawls the Hacker School website for Hacker Schooler name,
    info, and pictures. Takes username and password as arguments to login to
    site, as well as batch information (to narrow search). Stores list of
    tuples (name, picture, skills) in items attribute.

    """
    def __init__(self, username, password, batch):
        super(HackerSchoolerSpider, self).__init__(username, password)
        self.batch = batch

    def action(self, response):
        html = response.read()
        soup = lxml.html.soupparser.fromstring(html)  # could cache previous
        batch_select = "//ul[@id='" + self.batch + "']//li[@class='person']"

        names = soup.xpath(batch_select + "/div[@class='name']/a/text()")
        pics = soup.xpath(batch_select + "/a/img[@class='profile-image']/@src")
        skills = soup.xpath(batch_select + "/span[@class='skills']")

        names_raw = get_strs_from_lxml_list(names)
        pics_raw = get_strs_from_lxml_list(pics)
        skills_raw = [sk.text_content() for sk in skills]  # handle empties

        self.items = zip(names_raw, pics_raw, skills_raw)


def get_strs_from_lxml_list(lxml_objects):
    """Returns list of formatted strings from list of lxml objects."""
    return [obj.format() for obj in lxml_objects]
