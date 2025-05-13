from sys import argv
from Bio import SeqIO

'''This script takes as argv[1] a file containing one ID per line of sequences to be removed
   from a bigger dataset, passed as argv[2]. It prints on the terminal the number of sequences in the id list
   followed by the number of removed sequences.
'''


to_remove = argv[1]
dataset = argv[2]

with open(to_remove , 'r') as file:
    ids_to_rm = {line.strip() for line in file}

counter1 = 0 #keeps track of single ids to remove.
counter2 = len(ids_to_rm)

with open(dataset , 'r') as file1 , open('DATASET_all_kunitz_not_training.fasta' , 'w') as file2:
    for prot in SeqIO.parse(file1 , 'fasta'):
        if prot.id in ids_to_rm:
            counter1 = counter1 + 1
            continue
        else:
            SeqIO.write(prot , file2 , 'fasta')

print(counter2)
print(counter1)
        
