from selenium import webdriver
import getpass
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cookies", help="Turn on this flag if you have valid saved cookies",\
        action="store_true")
    return parser.parse_args()

def prompt_url():
    print("Welcome to Umich Lecture Scraper")
    print("Scrapes websites like: https://leccap.engin.umich.edu/leccap/site/sfa0sikeywiehigrodj")
    url = input("Enter leccap URL to scrape: ")
    print("Scraping...")
    return url

class DriverManager:
    def __init__(self, url):
        self.__driver = webdriver.Chrome()
        self.__driver.get(url)
        self.__url = url
        self.__args = parse_args()
        self.__s3_urls = []

    def __del__(self):
        print("Closing driver")
        self.__driver.close()

    def scrape(self):
        self.__login()
        self.__save_recording_urls()
        for url in self.__recording_urls:
            self.__visit_video(url)
        self.__save_s3_urls()

    def __login(self):
        if self.__args.cookies:
            self.__load_cookies()
            self.__driver.get(self.__url)
        else:
            self.__driver.implicitly_wait(60)
            self.__input_creds()

        self.__recordings = self.__driver.find_element_by_id('recordings')
        if not self.__args.cookies:
            self.__save_cookies()

    def __load_cookies(self):
        self.__cookies = []
        with open('curr_cookies.txt', 'r') as filehandle:
            for line in filehandle:
                currentPlace = line[:-1]
                self.__cookies.append(eval(currentPlace))
        for cookie in self.__cookies:
            self.__driver.add_cookie(cookie)

    def __save_cookies(self):
        self.__cookies = self.__driver.get_cookies()
        with open('curr_cookies.txt', 'w') as filehandle:
            for listitem in self.__cookies:
                filehandle.write('%s\n' % listitem)

    def __input_creds(self):
        uniqname = input("Please enter your uniqname: ")
        password = getpass.getpass("Please enter your password: ")
        self.__driver.find_element_by_id("login").send_keys(uniqname)
        self.__driver.find_element_by_id("password").send_keys(password)
        self.__driver.find_element_by_id("loginSubmit").click()
        print("Now please authenticate on Duo...")

    def __visit_video(self, url):
        self.__driver.get(url)
        self.__driver.implicitly_wait(12)
        self.__driver.find_element_by_class_name("viewer-overlay-play-btn").click()
        s3_url = self.__driver.find_element_by_tag_name('video').get_attribute('src')
        self.__s3_urls.append(s3_url)

    def __save_recording_urls(self):
        a_elts = self.__recordings.find_elements_by_class_name('list-group-item')
        self.__recording_urls = []
        for a_elt in a_elts:
            self.__recording_urls.append(a_elt.get_attribute('href'))

    def __save_s3_urls(self):
        with open('s3_url_list.txt', 'w') as filehandle:
            for s3_url in self.__s3_urls:
                filehandle.write('%s\n' % s3_url)

def main():
    url = prompt_url()
    driverManager = DriverManager(url)

    try:
        driverManager.scrape()
    except Exception as e:
        print("Unexcepted exception raised: " + str(e))

if __name__ == '__main__':
    main()
