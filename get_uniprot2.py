import requests
from sys import argv

'''This script takes as input a file containing Pdb entry IDs, and prints on the terminal
   the corss reference to the Uniprot database
'''

pdb_ids = []

#create a list containing all ids from the input file
with open(argv[1] , 'r') as file:
    for line in file:
        if line.startswith('>'):
            line = line.strip()
            end = line.find(':')
            pdb_ids.append(line[1:end])
        else:
            continue

#query for the pdb graphiql API. with this specific query we can retrive the cross-reference to uniprot

query =str('''{
  entries(entry_ids:%s) {
    polymer_entities {
      rcsb_polymer_entity_container_identifiers {
        uniprot_ids
      }
    }
  }
}''' %pdb_ids)
#all single quotes need to be changed to double quotes
query = query.replace("'" , '"')
query = requests.utils.requote_uri(query)
r = requests.get(f'https://data.rcsb.org/graphql?query={query}')
j = r.json()

for entry in j["data"]["entries"]:
    for entity in entry["polymer_entities"]:
        ids = entity["rcsb_polymer_entity_container_identifiers"]["uniprot_ids"]
        try: #some entries do not have any uniprot_id, resulting in a type error when trying to parse the contents of the dict
            for uniprot_id in ids:
                print(uniprot_id)
        except TypeError:
            continue
