import time
import requests

import pandas as pd

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def extract_data(soup):
    """
    Extracts and returns specific details such as name, address, contact person, telephone,
    and email from a BeautifulSoup object.
    """
    details = {'name': "", 'address': "", 'contact_person': "", 'telephone': "", 'email': ""}
    address_card = soup.find('span', class_='card-title', string=lambda x: x and 'Anschrift' in x)

    if address_card:
        # Get the parent div that contains all address info
        card_body = address_card.find_parent('div', class_='card-body')

        # Find the div after the title that contains the address
        address_div = card_body.find_all('div')[-2]  # Second to last div

        # Extract facility name
        facility_name = address_div.find('span', class_='fw-bold')
        details['name'] = facility_name.text.strip()

        # Extract all span elements
        spans = address_div.find_all('span')
        if len(spans) >= 3:
            add_1 = spans[1].text.strip()
            add_2 = spans[2].text.strip()
            details['address'] = add_1 + '\n' + add_2

    # Telephone
    telephone_elem = soup.find('a', href=lambda x: x and x.startswith('tel:'))
    if telephone_elem:
        details['telephone'] = telephone_elem.text

    # Email
    email_elem = soup.find('a', href=lambda x: x and x.startswith('mailto:'))
    if email_elem:
        details['email'] = email_elem.text

    # Get contact person
    contact_heading = soup.find('span', class_='h3 text-primary', string=lambda x: x and 'Ansprechperson' in x)
    if contact_heading:
        card = contact_heading.find_parent('div', class_='card')
        # Get name
        name_span = card.find('span', class_='card-title text-dark')
        details['contact_person'] = name_span.text

    return details


def get_location_details(locations):
    """
    Extracts location details from the provided web element.
    """
    divs_inside = locations.find_elements(By.CSS_SELECTOR, ".filter-item.col-md-6.col-lg-4.standort-append-item")
    print(f"Number of locations: {len(divs_inside)}")

    entries = []
    for idx, div in enumerate(divs_inside):

        if idx % 10 == 0:
            print(f"{idx} location details extracted.")
        try:
            a = div.find_element(By.CSS_SELECTOR, ".btn.btn-link.mt-auto.text-left.stretched-link.position-static")
            facility_url = a.get_attribute("href")
            response = requests.get(facility_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            entries.append(extract_data(soup))
        except:
            continue

    return entries


def click_button(driver, url):
    """
    Clicks a button continuously until the button is unavailable.
    """
    timeout = 10

    driver.maximize_window()
    driver.get(url)
    wait = WebDriverWait(driver, timeout)

    while True:
        try:
            button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-outline-primary.view-more-button")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(1)
            button.click()
            time.sleep(3)
        except Exception as e:
            print("Button not found", e)
            break

    locations = driver.find_element(By.CSS_SELECTOR, ".row.g-3.standorte-list")
    entries = get_location_details(locations)
    return entries


if __name__ == "__main__":
    driver = webdriver.Chrome()
    url = "https://awo-ol.de/meine-awo-karriere/awo-weser-ems/standorte-leistungen"
    entries = click_button(driver, url)
    driver.quit()

    df = pd.DataFrame(entries)
    df.to_csv('data/scraped_weser.csv', index=False)
