import json
import sys
import requests
from pyzotero import zotero

# import Zotero user details
from helper import library_id, library_type, api_key
# import Notion user detials
from helper import Notion_version, notion_url, Notion_API_Key



###############################################
###########   Zotero Functions   ##############
###############################################
def connectZot(library_id, library_type, api_key):
    """
    Connect to the Zotero library using API
    """
    zot = zotero.Zotero(library_id, library_type, api_key)
    return zot

def zotero_everything(zot, **filter):
    """
    Retrieves entier Zotero Library
    """
    if filter:
        items = zot.everything(zot.items(filter))
    else:
        items = zot.everything(zot.items())
    return items
    # print(json.dumps(items, indent = 2))


def zot_keepArticle(zot_library):
    """
    Removes entries that are attachments, notes, computerProgram and annotation from complete Zotero Library
    """
    zot_articles = []
    notKeep = ['attachment', 'note', 'computerProgram', 'annotation'] # Entry types to not keep

    for item in zot_library:
        if item['data']['itemType'] in notKeep:
            pass
        else:
            zot_articles.append(item)
    return zot_articles



def zot_getKeys(zot_library):
  """
  Extracts the keys from the complete Zotero Library
  """
  keys = []
  for item in zot_library:
      keys.append( item['data']['key'] )

  return keys


def zot_collections(zot):
    """
    Extracts collections from Zotero API
    """
    collections = zot.collections()
    return collections

def get_collection_keys(cleaned_zot_files):
    """
    Gets the collection (folder) id keys for each entry in the cleaned Zotero files
    """
    col_keys = []
    if 'collections' in cleaned_zot_files['data'].keys():
        if len(cleaned_zot_files['data']['collections']) > 1:
            for i in cleaned_zot_files['data']['collections']:
                col_keys.append(i)
        elif len(cleaned_zot_files['data']['collections']) == 1:
            col_keys.append(cleaned_zot_files['data']['collections'][0])
        else: pass

    return col_keys

def get_collections(collections, col_keys):
    """
    Matches the collection to the collection id key
    """
    col_out = ''
    if len(col_keys) > 1:
        for key in col_keys:
            for col in collections:
                if key in col['key']:
                    col_out = col_out + col['data']['name'] + '\n'
    elif len(col_keys) == 1:
        for col in collections:
            if col_keys[0] in col['key']:
                col_out = col_out + col['data']['name'] + ' '
    else: pass
    return col_out


def compareKeys(zotkeys, notkeys):
    """
    Compares the Zotero and Notion keys
    """
    keys = []

    for zkey in zotkeys:
        if zkey in notkeys:
            pass
        else:
            keys.append(zkey)

    return keys



def zot_returnItems(zot_library, keyIDs):
    """
    Takes a set of keys and returns the full Zotero library data for those keys
    """
    items = []

    for item in zot_library:
        if item['data']['key'] in keyIDs:
            items.append(item)
        else:
            pass

    return items

###############################################
###########   Notion Functions   ##############
###############################################

def not_getLibrary(url = notion_url,
                NOTION_API_KEY = Notion_API_Key,
                data = {},
                has_more = False,
                next_cursor = ''):
    """
    Retrieves Notion data base info
    """

    headers = {
                'Authorization': f"Bearer {NOTION_API_KEY}",
                'Content-Type': 'application/json',
                }

    if has_more == True:
        data =  {'start_cursor': next_cursor}
        data = json.dumps(data)
    else:
        data = data


    # Make API request to library
    response = requests.post(url, headers=headers, data=data)

    if response.reason == 'OK':
        return response.json()

    else:
        print('FAILED to retrieve Notion library: ', response.reason)


def not_getKeys(url = notion_url,
                NOTION_API_KEY = Notion_API_Key,
                data = {}):
    """
    Retrieves keys from Notion database as well as the parent dbID
    """
    Not_keys = []

    lib = not_getLibrary(url = url, NOTION_API_KEY = NOTION_API_KEY, data = data)

    for i in range(0, len(lib['results'])):
        Not_keys.append(lib['results'][i]['properties']['Z_ID']['rich_text'][0]['plain_text'])

    while lib['has_more'] == True:
        next_cursor = lib['next_cursor']

        lib = not_getLibrary(url = url,
                            NOTION_API_KEY = NOTION_API_KEY,
                            data = data,
                            has_more = True,
                            next_cursor = next_cursor)

        for ii in range(0, len(lib['results'])):
            Not_keys.append(lib['results'][ii]['properties']['Z_ID']['rich_text'][0]['plain_text'])

    return Not_keys


def not_dbID(url = notion_url,
            NOTION_API_KEY = Notion_API_Key,
            data = {}):
    '''
    Retrieves the parent dbID
    '''

    lib = not_getLibrary(url = url, NOTION_API_KEY = NOTION_API_KEY, data = data)

    dbID = lib['results'][0]['parent']['database_id']

    return dbID

# Need to do the main update notion function.

def returnAuthors(upload_file):
    """
    Finds the authors from a Zotero entery and returns a string
    """
    authors = upload_file['data']['creators']
    auth = ''
    for i in range(0, len(authors)):
        if 'firstName' in authors[i]:
            if i != (len(authors) - 1):
                auth = auth + authors[i]['lastName'] + ", " + authors[i]['firstName'] + '\n'
            else:
                auth = auth + authors[i]['lastName'] + ", " + authors[i]['firstName']
        else:
            if i != (len(authors) - 1):
                auth = auth + authors[i]['name'] + '\n'
            else:
              auth = auth + authors[i]['name']
    return auth

def returnTags(upload_file):
    """
    Finds the tags from a Zotero entry and returns a string with the tags
    """
    tags = ''
    pre_tags = upload_file['data']['tags']

    if len(pre_tags) == 0:
        pass
    elif len(pre_tags) == 1:
        tags = pre_tags[0]['tag']
    else:
        for tag in pre_tags:
            tags = tags + tag['tag'] + '\n'

    return tags


def not_newEntry(database_id, title, date, Z_ID, authors, tags, collection, NOTION_API_KEY,
                Notion_version):
    """
    Makes an API request to create a new entry in a Notion database
    """
    data = {
        "parent": {"database_id": database_id },
        "properties": {
        "Journal Article": {
          "type": "title",
          "title": [{ "type": "text", "text": { "content": title } }]
        },
        "Date": {'rich_text': [{
      'plain_text': date,
      'text': {'content': date, 'link': None},
      'type': 'text'}]
        },
        "Z_ID": {'rich_text': [{
      'plain_text': Z_ID,
      'text': {'content': Z_ID, 'link': None},
      'type': 'text'}]
        },
        "Author" : {'rich_text': [{
      'plain_text': authors,
      'text': {'content': authors, 'link': None},
      'type': 'text'}]
        },
        "Tags":{"rich_text":[{
            'plain_text': tags,
            'text':{'content': tags, 'link':None},
        'type': 'text'}]
        },
        "Collection":{"rich_text":[{
            'plain_text': collection,
            'text':{'content': collection, 'link':None},
        'type': 'text'}]
        }
      }
    }
    # Convert to json
    data = json.dumps(data)

    # Authentication headers
    headers = {
        'Authorization': f"Bearer {NOTION_API_KEY}",
        'Content-Type': 'application/json',
        'Notion-Version': Notion_version,
    }

    # UP UP AND AWAY
    response = requests.post('https://api.notion.com/v1/pages',
                            headers=headers, data=data)
    return response

def not_update_collection(page_id, collection_data):
    data = {
            "properties": {
            "Collection":{"rich_text":[{
                'plain_text': collection_data,
                'text':{'content': collection_data, 'link':None},
            'type': 'text'}]
            }
          }
        }

    data = json.dumps(data)
    headers = {
                'Authorization': f"Bearer {Notion_API_Key}",
                'Content-Type': 'application/json',
                'Notion-Version': Notion_version,
            }
    response = requests.patch(f'https://api.notion.com/v1/pages/{page_id}',
                                    headers=headers, data=data)

    if response.reason == 'OK':
        print(f'Page Updated')
    else:
        print(f'Failed: {response.reason}')


def not_collection_helper(notion_db, zotero_files, zotero_collections):
    for result in notion_db['results']:
        # Z_ID for the current Journal Article from notion
        zID = result['properties']['Z_ID']['rich_text'][0]['text']['content']

        # Pull the collection information
        if result['properties']['Collection']['rich_text'] ==  []: # Check if notino collection is empty
            n_collection = [] # Notion Collection is empty
        else:
            n_collection = result['properties']['Collection']['rich_text'][0]['plain_text']

        # Find the corrosponding collection items from Zotero
        for i in range(0, len(zotero_files)):
            if zID in zotero_files[i]['key']:
                ja =  zotero_files[i] # Journal Article
                col_keys = get_collection_keys(ja)
                z_collection = get_collections(zotero_collections, col_keys)
            else:
                pass

        # Check if the collection data matches
        if n_collection == z_collection:
            pass
        else:
            # Define Parameters to pass to requests()
            page_id = result['id']

            name = result['properties']['Journal Article']['title'][0]['plain_text']

            # Update collections function
            not_update_collection(page_id = page_id, collection_data = z_collection)
            print(f'Name ~ {name}')


def not_update_tags(page_id, tag_data):
    data = {
            "properties": {
            "Tags":{"rich_text":[{
                'plain_text': tag_data,
                'text':{'content': tag_data, 'link':None},
            'type': 'text'}]
            }
          }
        }

    data = json.dumps(data)
    headers = {
                'Authorization': f"Bearer {Notion_API_Key}",
                'Content-Type': 'application/json',
                'Notion-Version': Notion_version,
            }
    response = requests.patch(f'https://api.notion.com/v1/pages/{page_id}',
                                    headers=headers, data=data)

    if response.reason == 'OK':
        print(f'Page Updated')
    else:
        print(f'Failed: {response.reason}')


def not_tags_helper(notion_db, zotero_files):
    for result in notion_db['results']:
        # Z_ID for the current Journal Article from notion
        zID = result['properties']['Z_ID']['rich_text'][0]['text']['content']

        # Pull the collection information
        if result['properties']['Tags']['rich_text'] ==  []: # Check if notino collection is empty
            n_tags = [] # Notion Collection is empty
        else:
            n_tags = result['properties']['Tags']['rich_text'][0]['plain_text']

        # Find the corrosponding Tag items from Zotero
        for i in range(0, len(zotero_files)):
            if zID in zotero_files[i]['key']:
                ja =  zotero_files[i] # Journal Article
                z_tags = returnTags(ja)
            else:
                pass

        # Check if the collection data matches
        if n_tags == z_tags:
            pass
        else:
            # Define Parameters to pass to requests()
            page_id = result['id']

            name = result['properties']['Journal Article']['title'][0]['plain_text']

            # Update collections function
            not_update_tags(page_id = page_id, tag_data = z_tags)
            print(f'Name ~ {name}')

###############################################
######### Main Update Functions    ############
###############################################
def updateNotion(upload_files,
                database_id,
                collections,
                Notion_version,
                NOTION_API_KEY = Notion_API_Key
                ):
    """
    Main function to update Notion Database from a Zotero Library
    """
    complete = 0 # keep track of updates
    failed = 0 # keep track of failed updates

    for file in upload_files:

        # Title
        title = file['data']['title']

        # Authors
        authors = returnAuthors(file)

        #Date
        date = file['data']['date']

        #Z_ID
        Z_ID = file['data']['key']

        #Tags
        tags = returnTags(file)

        # Collection
        col_keys = get_collection_keys(file)

        collection_ = get_collections(collections, col_keys)

        response = not_newEntry(database_id, title, date, Z_ID, authors, tags, collection_, NOTION_API_KEY,
                            Notion_version)

        if response.reason == 'OK':
          print(f'Page Created  |  Name: {title}  |  Z_ID: {Z_ID}')
          complete = complete + 1
        else:
          print(f'Failed. Name: {title}. Response: ', response.text)
          failed = failed + 1

        print(f"{complete} entries updated  |  {failed} entries failed")



def updateCollections(cleaned_zotero_files, zotero_collections):
    has_more = True
    data = {}
    data = json.dumps(data)

    not_library = not_getLibrary(url = notion_url, NOTION_API_KEY = Notion_API_Key)

    not_collection_helper(not_library, cleaned_zotero_files, zotero_collections)

    has_more = not_library['has_more'] # Check if there is more to retreive from the notion db

    while has_more == True: #
        next_ = not_library['next_cursor']

        not_library = not_getLibrary(url = notion_url, NOTION_API_KEY = Notion_API_Key, has_more = True,
                                    next_cursor = next_)

        not_collection_helper(not_library, cleaned_zotero_files, zotero_collections)

        has_more = not_library['has_more']


    print('Update complete :D')

def updateTags(cleaned_zotero_files):
    not_library = not_getLibrary(url = notion_url, NOTION_API_KEY = Notion_API_Key)

    not_tags_helper(not_library, cleaned_zotero_files)

    has_more = not_library['has_more'] # Check if there is more to retreive from the notion db

    while has_more == True: #
        next_ = not_library['next_cursor']

        not_library = not_getLibrary(url = notion_url, NOTION_API_KEY = Notion_API_Key, has_more = True,
                                    next_cursor = next_)

        not_tags_helper(not_library, cleaned_zotero_files)

        has_more = not_library['has_more']


def syncEntries():
    message = '''
Starting to update Notion Database with entries from Zotero.

Some points to keep in mind:
- There needs to be at least one entry into the data base so that the parent database key can be retrieved.
- There needs to fake key in that fake entry for indexing reasons.
- If it not working then the Notion version number may need to be updated in the header.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n
    '''

    print(message)

    zot = connectZot(library_id = library_id, library_type = library_type, api_key = api_key)
    print('Connected to Zotero\n')

    print('Retreiving Zotero Files...\n')
    zot_files = zotero_everything(zot)

    print('Retreving Zotero Collections...\n')
    collections = zot_collections(zot)

    print('Cleaning Files')
    clean_files = zot_keepArticle(zot_files)

    print('Retrieving Keys\n')
    zot_keys = zot_getKeys(clean_files)

    #Got Notion Keys
    not_keys = not_getKeys()

    # Getting database ID
    databaseID = not_dbID()

    print('Comparing Keys\n')
    updateIDs = compareKeys(zot_keys, not_keys)

    if len(updateIDs) == 0:
        print('Notion up-to date')

    else:
        # Get update files
        print('Retrieving information for new entries\n')
        updateFiles = zot_returnItems(clean_files, updateIDs)

        # Update Notion DB
        print('Updating Notion Data Base\n')
        updateNotion(upload_files = updateFiles,
                    database_id = databaseID,
                    collections = collections,
                    Notion_version = Notion_version,
                    NOTION_API_KEY = Notion_API_Key)


        print('Update complete :D')
        print(f'{len(updateIDs)} Journal Articles Added')

def syncCollections():
    message = '''



~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n
    '''

    print(message)

    zot = connectZot(library_id = library_id, library_type = library_type, api_key = api_key)
    print('Connected to Zotero\n')

    print('Retreiving Zotero Files...\n')
    zot_files = zotero_everything(zot)

    print('Retreving Zotero Collections...\n')
    collections = zot_collections(zot)

    print('Cleaning Files')
    clean_files = zot_keepArticle(zot_files)

    updateCollections(cleaned_zotero_files = clean_files, zotero_collections = collections)

def syncTags():
    message = '''


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n
    '''

    print(message)

    zot = connectZot(library_id = library_id, library_type = library_type, api_key = api_key)
    print('Connected to Zotero\n')

    print('Retreiving Zotero Files...\n')
    zot_files = zotero_everything(zot)

    print('Cleaning Files')
    clean_files = zot_keepArticle(zot_files)

    updateTags(cleaned_zotero_files = clean_files)

    print('Update Complete')


if __name__ == '__main__':
    message = """

███████╗ ██████╗ ████████╗███████╗██████╗  ██████╗     ██████╗     ███╗   ██╗ ██████╗ ████████╗██╗ ██████╗ ███╗   ██╗
╚══███╔╝██╔═══██╗╚══██╔══╝██╔════╝██╔══██╗██╔═══██╗    ╚════██╗    ████╗  ██║██╔═══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
  ███╔╝ ██║   ██║   ██║   █████╗  ██████╔╝██║   ██║     █████╔╝    ██╔██╗ ██║██║   ██║   ██║   ██║██║   ██║██╔██╗ ██║
 ███╔╝  ██║   ██║   ██║   ██╔══╝  ██╔══██╗██║   ██║    ██╔═══╝     ██║╚██╗██║██║   ██║   ██║   ██║██║   ██║██║╚██╗██║
███████╗╚██████╔╝   ██║   ███████╗██║  ██║╚██████╔╝    ███████╗    ██║ ╚████║╚██████╔╝   ██║   ██║╚██████╔╝██║ ╚████║
╚══════╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝    ╚═╝  ╚═══╝ ╚═════╝    ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                                                                                                                     


Input 1 to update all entries. Input 2 to update tag information. Input 3 to update collection information. enter q to quit.

Input:\t"""
    user = input(message)

    while user not in ['1','2','3','q']:

        user = input('Incorrect input, try again:\t')

    if user == '1':
        syncEntries()
    elif user == '2':
        syncTags()
    elif user == '3':
        syncCollections()
    else:
        exit()
