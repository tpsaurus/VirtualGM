# importer.py

# imports
from bs4 import BeautifulSoup

#import the disease database
def importDisease(filename):
    with open(f'data/{filename}', 'r', encoding='utf-8') as file:  # open the file
        data_cache = []
        for line in file.readlines():
            # Strip the extra headers off of each line and split it up
            # NOT PERFECT
            # print(line)
            line = line.removeprefix('INSERT INTO ')
            linedata = line.split('VALUES ')
            prefix = linedata[0].split()[0].strip("`")
            # print(prefix)
            # print(linedata[1])
            data = linedata[1].split(',', 5)
            ID = data[0].removeprefix('(').strip("'")
            # print(editedtext)
            # print(data)

            #attempt at using beautiful soup to get data from the last cell
            #TODO - Parse data with Beautiful Soup
            soup = BeautifulSoup(data[5], "html.parser")
            text = soup.get_text()
            text = text.strip(r'\r')
            text = text.strip(r'\n')
            print(text)

            # Export the data from the line into a dictionary
            data_dict = {
                'Type': prefix,
                'ID': data[0].removeprefix('(').strip("'"),
                'Title': data[1],
                'Level': data[2],
                'Source': data[3],
                'Data': data[5],
                'URL': f"http://iws.mx/dnd/?view={prefix.lower()}{ID}"
            }
            # print(data[5])
            data_cache.append(data_dict) # add that dict to the list of dicts
    index = ['Type', 'ID', 'Title', 'Level', 'Source', 'Data', 'URL'] # the index
    return (data_cache, index, prefix) # return a tuple with the data, the index and the database title to be read by
    # the exporter


def importFeat(filename):
    with open(f'data/{filename}', 'r', encoding='utf8') as file:
        data_cache = []
        for line in file.readlines():
            # print(line)
            line = line.removeprefix('INSERT INTO ')
            linedata = line.split('VALUES ')
            prefix = linedata[0].split()[0].strip("`")
            # print(prefix)
            # print(linedata[1])
            data = linedata[1].split(',', 7)
            ID = data[0].removeprefix('(').strip("'")
            # print(editedtext)
            # print(data[7])
            data_dict = {
                'Type': prefix,
                'ID': data[0].removeprefix('(').strip("'"),
                'Title': data[1],
                'Tier': data[5],
                'Source': data[4],
                'Data': data[7],
                'URL': f"http://iws.mx/dnd/?view={prefix.lower()}{ID}"
            }
            # print(data_dict)
            data_cache.append(data_dict)
    index = ['Type', 'ID', 'Title', 'Tier', 'Source', 'Data', 'URL']
    return (data_cache, index, prefix)

# TODO - Fix the item URL. Need to manually check URLs to figure out who it builds it.
def importItem(filename):
    with open(f'data/{filename}', 'r', encoding='utf8') as file:
        data_cache = []
        for line in file.readlines():
            # print(line)
            line = line.removeprefix('INSERT INTO ')
            linedata = line.split('VALUES ')
            prefix = linedata[0].split()[0].strip("`")
            # print(prefix)
            # print(linedata[1])
            data = linedata[1].split(',', 9)
            ID = data[0].removeprefix('(').strip("'")
            # print(editedtext)
            # print(data)
            data_dict = {
                'Type': prefix,
                'ID': data[0].removeprefix('(').strip("'"),
                'Title': data[1],
                'Cost': data[2],
                'Level': data[4],
                'Category': data[5],
                'Source': data[8],
                'Text': data[9],
                'URL': f"http://iws.mx/dnd/?view={prefix.lower()}{ID}"
            }
            # print(data[9])
            data_cache.append(data_dict)
            index = ['Type', 'ID', 'Title', 'Cost', 'Level', 'Category', 'Source', 'URL']
    return (data_cache, index, prefix)


def importPower(filename):
    with open(f'data/{filename}', 'r', encoding='utf8') as file:
        data_cache = []
        for line in file.readlines():
            # print(line)
            line = line.removeprefix('INSERT INTO ')
            linedata = line.split('VALUES ')
            prefix = linedata[0].split()[0].strip("`")
            # print(prefix)
            # print(linedata[1])
            data = linedata[1].split(',',9)
            ID = data[0].removeprefix('(').strip("'")
            # print(editedtext)
            # print(data)
            data_dict = {
                'Type': prefix,
                'ID': data[0].removeprefix('(').strip("'"),
                'Title': data[1],
                'Level': data[2],
                'Action': data[3],
                'Class': data[7],
                'Source': data[6],
                'Data': data[9],
                'URL': f"http://iws.mx/dnd/?view={prefix.lower()}{ID}"
            }
            # print(data[9])
            data_cache.append(data_dict)

    index = ['Type', 'ID', 'Title', 'Level', 'Action', 'Class', "Source", 'Data', 'URL']

    return (data_cache, index, prefix)
