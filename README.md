# Team-19-Project
Large Scale Data Management Team Project

## Project Description

Barring a bunch of information no one wants to hear, I'll provide a short description of what this spaghetti code does:

Everything in this project is run on AWS:
the FastAPI project is hosted in an ec2 instance in AWS which is connected to an RDS PostgreSQL instance to hold data

The FastAPI is setup to be managed by systemd so we are able to use systemctl commands to start/stop/enable/check the status of the proccess.
Traffic forwarding is setup through nginx.

### Python stuff

The python script is setup to connect to the database using the psycopg-binary package which inserts and selects data from the database.

The files were deployed using winscp since I was too lazy to package up the files into a docker image and use AWS's ECR (Elastic Container Repository).
A list of endpoints for the API are listed under `Usage` in the next section.

Crawling is done using a combination of the requests library and bs4 (BeautifulSoup) library to send requests and parse HTML. The crawling function itself is a recursive function that runs for the `depth` specified in the request, although depths larger than 2 tend to take a VERY LONG TIME to process since the URLs to parse likely doubles or even grows exponentially with each increment in depth.

### PostgreSQL Database stuff

Initialization of the database itself was done manually using dbeaver and connecting to the database to initialize the database.
Tables were created using the sqlalchemy python package which drastically reduces the amount of sql queries that has to be written since we can just use sqlalchemy methods to select, update, drop, etc.

In our web crawler application, two primary tables are used to store data about URLs and the links found on those URLs. Here is a detailed description of each table, including their structure and the relationships between them:

1. URL Table
Description: This table stores information about each URL that the crawler visits. It is designed to track whether a URL has been crawled and to store the root URL for potential recursive crawling.

Columns:
id (Integer): A unique identifier for each entry. This is the primary key of the table.
url (String): The actual URL string. This field is marked as unique to prevent duplicate entries of the same URL.
is_crawled (Boolean): A flag indicating whether the URL has been crawled. This helps in managing the crawling process, ensuring that URLs are not re-crawled unnecessarily.
Relationships:

links (relationship): A one-to-many relationship with the Link table. Each URL can have multiple links associated with it, representing the links found on that URL's page.

2. Link Table
Description: This table stores the links found on each crawled URL. It includes the link itself and the title of the link, if available. This table is used to record all the hyperlinks extracted from the pages that the crawler visits.

Columns:
id (Integer): A unique identifier for each link entry. This is the primary key of the table.
title (String): The text of the link as seen on the webpage, which often serves as the anchor text.
url (String): The hyperlink itself. This URL may be absolute or resolved from a relative link based on the URL of the page where it was found.
parent_id (Integer, ForeignKey): A foreign key linking back to the URL table, identifying which URL this link was found on.
Relationships:

parent (relationship): A many-to-one relationship back to the URL table. This establishes a link back to the URL that contains this hyperlink, allowing for a hierarchical structure of data where you can trace back links to their source URL.
Database Schema Relationships Overview
These tables are structured to efficiently support the data needs of a web crawler:

The URL table acts as the main entry for each unique page visited by the crawler. It tracks whether the page has been crawled, which is crucial for managing the crawl depth and preventing unnecessary re-crawling.
The Link table extends from the URL table by recording all links found on each page. The parent_id column creates a direct relationship back to the URL they were found on, which is essential for understanding the structure of the website and for potential further crawling of those links.
This setup allows for a relational approach to store and query crawled data. You can easily find all links associated with a particular URL, or conversely, identify the source URL of a particular link. This kind of structure is also useful for recursive crawling processes, where links from one page lead to further pages to be crawled.

## Usage
### Starting a Crawl

Send a GET request to the /crawl/ endpoint with the URL and optional depth parameter:
`GET /crawl/?url=https://example.com&depth=1`
or 
`http://18.188.166.149/crawl/?url=https://example.com&depth=1`

### Searching Indexed URLs
Send a GET request to the /search/ endpoint with an optional query parameter:
`GET /search/?query=SomeQuery`
or 
`http://18.188.166.149/search/?query=SomeQuery`

### Resetting all indexed URLs
Send a GET request to the /reset/ endpoint to clear the tables of each URL entry:
`GET /reset/`
or 
`http://18.188.166.149/reset/`

# Getting started (locally)

To set this project up locally, you'll need to run the following commands:

Setting up the VENV
Run:
```
pip3 install virtualenv

python3 -m venv env

source env/bin/activate
```

to install the requirements:
```
pip3 install -r requirements.txt
```

to run the webserver:
```
uvicorn main:app --reload
```
