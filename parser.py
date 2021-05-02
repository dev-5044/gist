import json
import csv
from time import sleep
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup as bs
from openpyxl import load_workbook
import requests

from browser import Browser


class Parser:

    current_position = list()
    current_position.append([
        'Talent',
        'Recruiter',
        'Recruitment',
        'Recruiting',
        'Sourcing',
        'Sourcer'])

    current_position.append([
        'people',
        'HR',
        'human'
    ])

    current_position.append([
        'Operations',
        'Assistant',
        'Office'
    ])

    current_position.append([
        'COO',
        'CEO',
        'Founder',
        'Co-Founder'
    ])

    RUCAPTCHA_KEY = "################"


    add_input_script = """
    var inp = document.createElement('input');
    inp.type = 'submit';
    inp.value = 'send';
    inp.id = 'send_token';
    document.getElementById('captcha-form').appendChild(inp);
    """

    def __init__(self, **kwargs):
        self.parser = Browser(**kwargs)
        self.parser.browser.get('https://www.google.com.ua/')

    def solve_recaptcha(self):
        self.parser.browser.execute_script(self.add_input_script)
        send_token_input = self.parser.browser.find_element_by_id('send_token')
        text_area_for_token = self.parser.browser.find_element_by_id('g-recaptcha-response')
        self.parser.browser.execute_script("document.getElementById('g-recaptcha-response').style.display = 'inline';")
        cookies = self.parser.browser.get_cookies()
        cookies_to_send = str()
        for cookie in cookies:
            # print(cookie)
            for key in cookie.keys():
                cookies_to_send += f"{key}:{cookie[key]};"
        html = self.parser.browser.page_source
        bs_obj = bs(html, 'html5lib')
        recaptca_tag = bs_obj.find('div', {'class': 'g-recaptcha', 'id': 'recaptcha'})

        data_sitekey = recaptca_tag['data-sitekey']
        data_s = recaptca_tag['data-s']
        data_callback = recaptca_tag['data-callback']
        page_url = self.parser.browser.current_url
        req_str = f"https://rucaptcha.com/in.php?" \
                  f"key={self.RUCAPTCHA_KEY}&" \
                  f"method=userrecaptcha&" \
                  f"googlekey={data_sitekey}&" \
                  f"data-s={data_s}&" \
                  f"cookies={cookies_to_send}&" \
                  f"pageurl={page_url}&" \
                  f"json=1&" \
                  f"debug_dumps=1"
        # if we want to use proxy, we should use this request url
        '''
        req_str = f"https://rucaptcha.com/in.php?" \
                  f"key={RUCAPTCHA_KEY}&" \
                  f"method=userrecaptcha&" \
                  f"googlekey={data_sitekey}&" \
                  f"data-s={data_s}&" \
                  f"proxy={AUTH}@{PROXY}&" \
                  f"proxytype=HTTPS&" \
                  f"pageurl={page_url}&" \
                  f"json=1&" \
                  f"debug_dumps=1"
        '''
        req_ans = requests.get(req_str)
        response = req_ans.text
        response = json.loads(response)
        if response['status'] == 1:
            id = response['request']
            req_res = f"https://rucaptcha.com/res.php?" \
                      f"key={RUCAPTCHA_KEY}&" \
                      f"action=get&" \
                      f"id={id}&" \
                      f"json=1"
            print("Our request is processing")
            print(f"id = {id}")
            while True:
                sleep(20)
                res = requests.get(req_res).text
                res = json.loads(res)
                if res['status'] == 1:
                    print("Captcha is solved successfully")
                    token = res['request']
                    add_cookies = res['cookies']
                    for key in add_cookies.keys():
                        if add_cookies[key] == 'True':
                            add_cookies[key] = True
                            continue
                        if add_cookies[key] == 'False':
                            add_cookies[key] = False
                            continue
                        if add_cookies[key].isdigit():
                            add_cookies[key] = int(add_cookies[key])
                    text_area_for_token.send_keys(token)
                    send_token_input.click()
                    return True
                if res['request'] == 'ERROR_CAPTCHA_UNSOLVABLE':
                    self.parser.browser.refresh()
                    self.solve_recaptcha()
                    break
                print(f"{res['request']} -- Waiting")

    def check_current_position(self, title):
        for cur_pos in self.current_position:
            for pos in cur_pos:
                if pos in title:
                    return True
        return False

    def get_google_search_res(self, query):
        search_box = self.parser.browser.find_element_by_name('q')
        search_box.send_keys(Keys.CONTROL + 'a')
        search_box.send_keys(Keys.DELETE)
        search_box.send_keys(query)
        sleep(2)
        search_box.submit()
        sleep(2)
        try:
            search_com = self.parser.interaction_with('//div[@class="g"]/div/div/div[2]')
        except TimeoutException:
            self.solve_recaptcha()
        print('hey', [i.text.split('\n')[0].split(' · ‎')[-1] for i in search_com])
        search_div = self.parser.interaction_with('//div[@class="g"]')
        res = []
        if not search_div:
            self.solve_recaptcha()
        for element, com in zip(search_div, search_com):
            html = element.get_attribute('innerHTML')
            soup = bs(html, 'html5lib')
            h3 = soup.h3.get_text()
            splitted_h3 = h3.split(' - ')
            if len(splitted_h3) == 1:
                another_split = h3.split(' – ')[0]
                if len(another_split) == 1:
                    continue
                name = another_split[0]
                print(name)
                job_title = another_split[1]
            else:
                name = splitted_h3[0]
                job_title = splitted_h3[1]
                print(job_title)
            # если у нас нет текущих слов в job title
            # то пропускаем
            if not self.check_current_position(job_title):
                return None
            if 'href' in soup.a.attrs:
                link = soup.a['href']
            num = search_div.index(element) + 1
            res.append({'name': name, 'title': job_title,
                        'link': link, 'num': num,
                        'comp_from_google': com
                        })
        return res


    def get_comp_title(self, url):
        linkedin_browser = Browser(gui=True, profile='linkedin')
        linkedin_browser.browser.get(url)
        try:
            name = linkedin_browser.interaction_with('//a[@class="pv-top-card--experience-list-item"]')[0].text.strip()
        except TypeError:
            name = linkedin_browser.interaction_with('//a[@class="pv-top-card--experience-list-item"]').text.strip()
        linkedin_browser.browser.quit()
        return name


    def find_names(self, names_list):
        with open('res_names.csv', 'a') as csv_file:
            fieldnames = [
                          'name', 'title', 'num', 'comp_from_google',
                          'comp_title', 'link', 'word'
                          ]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for comp_title in names_list:
                cur_pos_str = '" OR "'.join(self.current_position[0])
                cur_pos_str = f'"{cur_pos_str}"'
                query = f'(intitle:"{comp_title}") (intitle:{cur_pos_str})  site:linkedin.com/in/'
                google_res = self.get_google_search_res(query)
                if google_res:
                    for res in google_res:
                        url = res['link']
                        res['word'] = query
                        res['comp_titles'] = self.get_comp_title(url)
                        writer.writerow(res)
