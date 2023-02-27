# Importing modules for web scraping
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import pandas as pd
from selenium.common.exceptions import ElementClickInterceptedException


# Create class for OOP
class WebScrape:
    # Initialize the class with your driver path
    def __init__(self, your_driver_path):
        # Specifying the driver path
        driver_path = Service(your_driver_path)
        # Initializing Chrome web driver
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        self.driver = webdriver.Chrome(service=driver_path, options=options)
        # Maximizes the windows when webdriver is opened
        self.driver.maximize_window()

    # Method that automatically scrolls down to the bottom of the page when called to click on a certain button
    def scroll(self):
        scrollable = self.driver.find_element(by=By.CLASS_NAME, value="is-upgraded")
        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)

    # Checking whether there is a next page in the current page
    def is_next_page(self):
        span = self.driver.find_elements(By.CSS_SELECTOR, ".mdc-button .mdc-button__label")
        for element in span:
            if element.text == "NEXT":
                return True
        return False

    # Merging to dictionary
    def merge(self, dict1, dict2):
        result = dict1 | dict2
        return result

    # Recommendation-- put r in the front of file path, "r" means Raw String, without it error might occur
    # Call this method in the main.py with the file path of your own and from_year, and to_year
    def scrape(self, file_path, from_year, to_year):
        # From start of space mission launches which is 1957
        # URL format of the website, for each year the last part of url changes
        space_url = f"https://nextspaceflight.com/launches/past/?search={from_year}"
        # Opening the webdriver
        self.driver.get(space_url)
        # Initializing three list to append, final will be the list that we are going to convert it to data frame
        # then csv
        front = []
        back = []
        final = []
        # While year is until this year
        while from_year <= to_year:
            try:
                organization = self.driver.find_elements(By.XPATH,
                                                         "/html/body/div/div/main/div/div/div/div/div/div/div/div/div/div/div/span")
                location = self.driver.find_elements(By.CLASS_NAME, "mdl-card__supporting-text")
                date = self.driver.find_elements(By.CLASS_NAME, "mdl-card__supporting-text")
                detail = self.driver.find_elements(By.CLASS_NAME, "header-style")
                # num_spaceship_per_page gets all the div that contains each space mission information
                # It will get the total mission launches count per page
                num_spaceship_per_page = self.driver.find_elements(By.CLASS_NAME, "mdl-card__title")
                # Until the total mission launches in the page
                for i in range(len(num_spaceship_per_page)):
                    # If statement for preventing additional data collection. Some space mission details contains number
                    # that equals to year so preventing this to happen if not found then
                    if detail[i].text.find(f'{from_year}') == -1:
                        # Append organization, location, date, and detail to front list as a dictionary
                        front.append({
                            "Organization": organization[i].text,
                            "Location": location[i].text.split("\n")[1],
                            "Date": date[i].text.split("\n")[0],
                            "Detail": detail[i].text,
                        })
                detail_keys = self.driver.find_elements(By.CLASS_NAME, "mdc-button")
                # for each detail key in the page
                for key in detail_keys:
                    # only click when the key text is details
                    if key.text == "DETAILS":
                        key.click()
                        rocket_status = \
                            self.driver.find_element(By.XPATH,
                                                     "/html/body/div/div/main/div/section/div/div/div/div[2]").text.split(
                                ":")[
                                1]
                        price = \
                            self.driver.find_element(By.XPATH, "/html/body/div/div/main/div/section/div/div/div/div[3]")
                        # Sourcing out wrong data collection. So if the price.text doesn't start with P, it means it is
                        # not a price value. And a lot of mission doesn't contain price information.
                        if price.text[0] == "P":
                            price = price.text.split(":")[1].replace("$", "").split()[0]
                        else:
                            price = None
                        mission_status = self.driver.find_element(By.XPATH,
                                                                  "/html/body/div/div/main/div/section/h6["
                                                                  "@class='rcorners status']").text
                        # Append rocket_status, price, mission_status to back list as a dictionary
                        back.append({
                            "Rocket_status": rocket_status,
                            "Price": price,
                            "Mission_status": mission_status
                        })
                        # Go back one step to collect all data for each rocket
                        self.driver.back()
                # Finally append, front and back list by merging two list with merge function into final for the length
                # of front
                for i in range(len(front)):
                    final.append(self.merge(front[i], back[i]))
            # Selenium is sensitive, this exception is just for continuous flow of web scarping
            # Try not to do other operation on the computer while selenium is scraping data
            except IndexError:
                continue
            except ElementClickInterceptedException:
                continue
            # This code need to execute despite any condition
            finally:
                # If there is next page on the current year, scroll down and click the next button
                if self.is_next_page():
                    self.scroll()
                    self.driver.find_element(By.XPATH, "/html/body/div/div/main/div/div/div/span/div/button").click()
                # If there is no next page move on to the next year
                else:
                    from_year += 1
                    # Finding the search input field
                    search = self.driver.find_element(By.ID, "search_field")
                    # Clear input in the search field
                    search.clear()
                    # Move to the next year by sending the year value into the search field
                    search.send_keys(from_year)
                    self.driver.find_element(By.CLASS_NAME, "btn-outline-danger").click()
                    # Emptying front and back without this the data will be cumulative
                    front = []
                    back = []
        # After the while loop create a data frame from the final list
        df = pd.DataFrame(final)
        # Then convert it into csv file
        df.to_csv(file_path)


