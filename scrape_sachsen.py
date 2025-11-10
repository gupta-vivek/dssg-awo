import time

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def click_checkboxes(driver):
    """Click all filter checkboxes and return the page source."""

    URL = "https://einrichtungen.awo-sachsen.de/index.php?search_term=&listMode=detail"
    TIMEOUT = 10

    driver.maximize_window()
    driver.get(URL)
    wait = WebDriverWait(driver, TIMEOUT)  # wait for the page to load

    # Check all checkboxes
    num_checkboxes = 13
    for i in range(1, num_checkboxes + 1):
        elem = wait.until(EC.element_to_be_clickable((By.NAME, f"entry_landkreis_filter[{i}][{i}]")))
        elem.click()
        print(f"Clicked - {i}")
        time.sleep(3)  # Wait for the page to update

    time.sleep(5)  # Wait for the page to update. Just for safety

    return driver.page_source


def parse_entry(entry):
    """Parse a single entry record."""
    record = {'name': entry.find('a').text.strip(), 'address': "", 'contact_person': "", 'telephone': "", 'fax': "",
              'email': "", 'website': "", 'organisation': "", "organisation_website": ""}

    result_address = entry.find('div', class_='resultAdresse')
    known_fields = {'Telefon:': 'telephone', 'Fax:': 'fax', 'EMail:': 'email', 'Web:': 'website'}

    record['address'] = result_address.contents[0].text.strip() + "\n" + result_address.contents[2].text.strip()

    num = 5
    if (len(result_address.contents[num].text) > 0) and (result_address.contents[num].text.strip() not in known_fields):
        record['contact_person'] = result_address.contents[num].text.strip()
        num += 1

    while num < len(result_address.contents) - 1:
        content = result_address.contents[num]
        cont_text = content.text.strip()
        if len(cont_text) > 0 and cont_text in known_fields:
            record[known_fields[cont_text]] = result_address.contents[num + 1].text
            num += 1
        num += 1

    organisation = result_address.contents[-2]
    record['organisation'] = organisation.text.strip()
    record['organisation_website'] = organisation.get('href')

    return record


def collect_entries(html_file: str):
    """Parse HTML file and extract all entry records."""

    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    lis = soup.find('ul', id='resultList').find_all('li')
    records = [parse_entry(entry) for entry in lis]

    return records


if __name__ == "__main__":
    driver = webdriver.Chrome()
    page_source = click_checkboxes(driver)
    driver.quit()

    html_file = "page_source.html"
    # Save the page source to an HTML file
    # with open(html_file, "w", encoding="utf-8") as f:
    #     f.write(page_source)

    records = collect_entries(html_file)

    df = pd.DataFrame(records)
    df.to_csv('data/scraped_sachsen.csv', index=False)
