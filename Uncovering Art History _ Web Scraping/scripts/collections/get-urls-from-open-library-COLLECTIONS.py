import requests
from bs4 import BeautifulSoup
import csv

# HTTP headers that allow our scraper to appear more "human"
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:78.0)   Gecko/20100101 Firefox/78.0", 
"Referer": "https://www.google.com"}

# Base url to enter search query
url = "https://openlibrary.org/search/inside/"

# Search query
parameters = {'q': '\"Archives of American Art\"'}

# Fieldnames for final csv
fieldnames = ['title', 'url', 'author', 'date_published', 'publisher', 'snippets_url', 'number_of_snippets', 'snippets']

# Some global values for ease of reading throughout this script
url_column_index = 1
search_results_csv = "collections\\collections-search-results.csv"

# CHANGE this variable if more search result pages have been added
# To check, go to https://openlibrary.org/search/inside?q=%22Archives+of+American+Art%22
search_results_page_end = 335


'''

This is a function that loops through search result pages for the query
"Archives of American Art" and grabs relevant metadata where url is the
base url for searching by text contents.

In our case, the url should always be "https://openlibrary.org/search/inside/".

'''
def get_items(url):

    # Keep track of new search results
    counter = 0

    base_url = 'https://openlibrary.org'

    # This format is easier for the computer to read in a url
    encoded_url ="%22Archives+of+American+Art%22"

    # loop through search result pages
    for page in range(1, search_results_page_end):

        # Specify page number for search query
        parameters['page'] = str(page)

        # Request page
        r = requests.get(url, params=parameters, headers=headers)
        # Progress check
        print(r.status_code, r.url)

        # Create beautiful soup object which allows us to parse through the HTML
        soup = BeautifulSoup(r.text, 'html.parser')

        # Loop through results
        for result in soup.find_all(class_='sri__main'):

            # Create dictionary for item where each key, value pair is a metadata field and value
            # Example: {'author': Roy Rosenzweig'}
            item_dict = {}

            # Grab url to full item and its metadata in Open Library and save to dictionary
            item_url = base_url + result.find(class_='results')['href']

            # Check if search result is new
            already_exists = check_if_new(item_url, url_column_index=url_column_index)

            # If result already captured, skip
            if already_exists:

                continue

            # If result is new, add to csv
            else:

                snippets = []

                item_dict['number_of_snippets'] = 0
                item_dict['snippets'] = snippets

                counter += 1

                print('new search result! adding', item_url, 'to csv')

                try:
                    # Try to find author information and add to dictionary
                    author = result.find(class_='bookauthor').text.strip().replace('\n', '').replace('by ', '')

                    # Skip item if author is AAA
                    if "Archives of American Art" in author:
                        print('AAA printed this! it doesn\'t count! skipping', item_url)
                        continue
                    else:
                        # If author is not AAA, continue with adding item
                        item_dict['author'] = result.find(class_='bookauthor').text.strip().replace('\n', '').replace('by ', '')
                except:
                    # If author not found, save value as "Not found"
                    item_dict['author'] = "Not found"

                item_dict['url'] = item_url

                # Create empty snippet list
                snippets = []

                # Find container with link to snippets viewer
                snippets = result.find(class_='fsi-snippet__main fsi-snippet__full-results')

                # Grab the url from snippets container
                snippets_url = snippets.find(class_='fsi-snippet__link')['href']

                # Reformatting of url to make it easier to read in csv
                snippets_url = snippets_url.split('"')[0]
                snippets_url = snippets_url + encoded_url

                # Add snippets url to dictionary
                item_dict['snippets_url'] = snippets_url

                # Call function that grabs more metadata from individual item's full page
                more_metadata = get_metadata_from_item(item_url)

                # Add the metadata captured above to our item dictionary
                item_dict.update(more_metadata)

                # Add completed row to search-results.csv
                with open(search_results_csv, "a", newline="", encoding='utf-8') as f:
                    w = csv.DictWriter(f, fieldnames)
                    w.writerow(item_dict)
        
    print(counter, "new search results found and added to csv!")


'''

This is a function that follows an individual item's url in Open Library
and grabs more specific metadata including title, date published, and publisher,
where path is the path to the indiviudal item page.

Returns a dictionary of metadata as key, value pairs.

An example of an item path would be: "https://openlibrary.org/books/OL823874M/Government_and_art".

'''
def get_metadata_from_item(path):

    # Create empty metadata dictionary
    metadata = {}

    # Request item page
    r = requests.get(path, headers=headers)
    # Progress check
    print(r.status_code, r.url)

    # Create beautiful soup object which allows us to parse through the HTML
    soup = BeautifulSoup(r.text, 'html.parser')


    try:
        # Try to find title information and add to dictionary
        metadata['title'] = soup.find('h1', class_='work-title').text
    except:
        # If title not found, save value as "Not found"
        metadata['title'] = "Not found"
    try:
        # Try to find date published information and add to dictionary
        metadata['date_published'] = soup.find(attrs={'itemprop': 'datePublished'}).text
    except:
        # If date published not found, save value as "Not found"
        metadata['date_published'] = "Not found"

    try:
        # Try to find publisher information and add to dictionary
        metadata['publisher'] = soup.find(attrs={'itemprop': 'publisher'}).text
    except:
        # If publisher not found, save value as "Not found"
        metadata['publisher'] = "Not found"

    return metadata

'''

This function will add an item to our existing csv as one row,
where data is the list of search result items, filename is the name
of the csv file we want to write to, and fieldnames is the list of
field names we want to capture.

Does not return a value.

'''
def items_to_csv(data, filename, fieldnames):
     
     # Open file and write item to dictionary
     with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
          writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
          writer.writeheader()
          writer.writerows(data)


'''

This function checks if a search result is already in our search-results.csv,
where url is the item's unique url and column_index is the index of the url
column in the csv to match against.

Returns True or False.

'''
def check_if_new(url, url_column_index):

    # Open the file in read-only mode
    with open(search_results_csv, 'r', encoding='utf-8') as csv_file:

        # Create a CSV reader object
        reader = csv.reader(csv_file)

        # Skip the first line with column names
        next(reader)

        # Generate a list of all values in url column
        urls = [row[url_column_index] for row in reader]

        # Check if url already exists in column, returns True if any matches are found
        already_exists = any(u == url for u in urls)

        return already_exists

# Call our function! 
get_items(url)