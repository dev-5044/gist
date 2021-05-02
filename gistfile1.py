from parser import Parser


pars = Parser(gui=True)
with open('search_company_name.txt', 'r') as file:
    lines = file.readlines()
try:
    pars.find_names([i.replace('\n', '') for i in lines])
except KeyboardInterrupt:
    pars.parser.browser.quit()
