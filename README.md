# Zotero2Notion
This script takes advantage of the new Notion API to sync a notion database to a Zotero Library. 

## Set-up
### Python
Packages:

- json
- requests
- pyzotero
  - https://github.com/urschrei/pyzotero


### Zotero API
Generate and setup a Zotero API key: https://www.zotero.org/settings/keys

Fill in the details in the helper.py file.

### Notion API

Follow steps 1 and 2 in : https://developers.notion.com/docs/getting-started.

Fill in details in the hellper.py file.

### Setting up a Notion Database
The Notion Database must have the following fields and feild-types.

- Journal Article 
  - Type: Title
- Date 
  - Type: Text
- Z_ID 
  - Type: Text
- Author
  - Type: Text
- Tags
  - Type: Text
- Collection
  - Type: Text


## Example
<img width="1680" alt="Screenshot 2021-07-13 at 13 45 16" src="https://user-images.githubusercontent.com/73599839/125446302-fe9369f7-465b-40e4-a862-cea41f2d688f.png">
