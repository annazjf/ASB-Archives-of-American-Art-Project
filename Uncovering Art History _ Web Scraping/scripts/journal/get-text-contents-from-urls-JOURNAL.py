from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import furl

# HTTP headers that allow our scraper to appear more "human"
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0)   Gecko/20100101 Firefox/78.0", 
"Referer": "https://www.google.com"}

# The name of the file we are working with. This will likely be 'search-results.csv' generated from the get-urls-from-open-library.py script
filename = 'journal-search-results.csv'

# # Some global values for ease of reading throughout this script
url_column_index = 1
snippets_url_column_index = 5

'''

This function takes our csv file of search results and appends snippets
information to new rows.

'''
def get_text_contents(file):

    # Open the file in read-only mode
    with open(file, 'r', encoding='utf-8') as csv_file:

        # Create a CSV reader object
        reader = csv.reader(csv_file)

        # Loop through rows in csv
        for row in reader:

            # Check if row is new (i.e. are snippets empty?)
            if row[len(row) - 2] == '0' and row[len(row) - 1] == '[]':

                # If new, call function that adds snippets to row
                get_snippets_from_url(row)

            # Otherwise, continue
            else:
                continue

'''

This function "clicks on" the snippets url from a new row and grabs snippets
with "Archives of American Art Journal" that appear in the full text. It returns a full
list of all snippet contents. If there are any urls that the reader cannot
pull from, they'll be noted in a separate file called issues.txt.

Example url: https://archive.org/stream/newhampshirescen00slsn?ref=ol&access=1#search/%22Archives+of+American+Art+Journal%22

'''
def get_snippets_from_url(row):

    # Create empty list to hold snippets information
    snippets = []

    # Change Selenium setting to headless mode to avoid new browser tabs popping up on screen
    # CHANGE if using a browser other than Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    # Encode url to replace special characters
    encoded_url = furl.furl(row[snippets_url_column_index]).url

    # Progress check
    print('grabbing snippets for', row[url_column_index])

    # Create driver session
    driver = webdriver.Chrome(options)
    # Send driver to url (i.e. open up the page)
    driver.get(encoded_url)
    # Have driver wait for max 10 seconds for all page features to load
    driver.implicitly_wait(10)

    try:

        # Follow shadow-root trail to get to the list of text snippets
        root1=driver.find_element(By.CSS_SELECTOR, "ia-book-theater[class='focus-on-child-only']").shadow_root
        root2=root1.find_element(By.CSS_SELECTOR, "ia-bookreader[class='focus-on-child-only']").shadow_root
        root3=root2.find_element(By.CSS_SELECTOR, "iaux-item-navigator").shadow_root
        root4=root3.find_element(By.CSS_SELECTOR, "ia-menu-slider").shadow_root
        root5=root4.find_element(By.CSS_SELECTOR, "ia-book-search-results").shadow_root

        # Isolate each snippet and page number
        all_items = root5.find_elements(By.CSS_SELECTOR, "p")

        # Create list of snippets
        # Each list item is formatted as such:
            # {'Page #': 'Snippet Content'}
            # Example: {'Page 15': 'Lockwood de Forest Papers, 1858-1978, Archives of American Art, Smithsonian Institution, Washington, D.C.'}
        snippets = [{all_items[i].text: all_items[i+1].text} for i in range(0, len(all_items), 2)]

        # Add number of snippets and snippets content to row
        row[len(row)-1] = snippets
        row[len(row)-2] = len(snippets)

        # Progress check
        print('found', str(len(snippets)), 'snippets!')

        # Rewrite row to file
        write_new_row(row, filename)

        # Close driver
        driver.close()

    # If there are issues...
    except:

        # Add url to issues.txt 
        with open('issues.txt', 'a', newline='', encoding='utf-8') as f:
            f.write(row[url_column_index] + '\n')
            f.close()

        # Feedback
        print(f"could not get snippets for {row[url_column_index]}")

        # Close driver
        driver.close()


'''

This function adds snippets information for a new row into our existing
journal-search-results.csv, where new_row is the new row and file is the
name of the file we're reading from and writing to.

'''
def write_new_row(new_row, file):

    # Create empty list of rows to "rebuild" csv
    rows = []

    # First, open file and read it
    with open(file, 'r', encoding='utf-8') as f:

        # Create csv reader object
        reader = csv.reader(f)

        # Loop through rows and add to our list
        for row in reader:

            # Replace new row
            if row[url_column_index] == new_row[url_column_index]:
                rows.append(new_row)

            # Keep all other rows the same
            else:
                rows.append(row)

    # Now, open the file again in write mode
    with open(file, 'w', newline='', encoding='utf-8') as f:

        # Create csv writer object
        writer = csv.writer(f)

        # Rewrite csv
        writer.writerows(rows)

# Execute functions above
get_text_contents(filename)