1) The following script contains all the commands and a brief description explaining them.
2) First download proteins from the pdb that had resolution <= 3.5 PFAM id PF00014 , Polymer entity sequence lenght <=80 and >=45 using a custom
   report that featured: ( PDB id, Entry Id , Auth Asym ID , Annotation Identifier , polymer entity id, Sequence ). The report has been downloaded in the .csv format
3) Transformed the report in a FASTA format file using the command:  
`cat kunitz_pdb_download_skip_two_lines.csv cat rcsb_pdb_custom_report_20250503062943.csv | tr -d '"' |awk -F ',' '{if (length($2)>0) {name=$2}; print name ,$3,$4,$5}'| grep PF00014 |       awk '{print ">"$1"_"$3; print $2}' > pdb_kunitz.fasta`
5) Generate clusters of similar sequences using the CD-HIT program with the command:   
`cd-hit -i pdb_kunitz.fasta -o kunitz_clustered.clst`
6) Obtain the representative proteins ids for each cluster with the command:  
`clstr2txt.pl kunitz_clustered.clst.clstr | awk '{if ($5==1) print $1}' > pdb_kunitz_representative.ids`
7) Retrieve the sequences corresponding to those ids, and put them all in a fasta file with the command:  
`for i in $(cat pdb_kunitz_representative.ids ); do grep -A 1 "^>$i" pdb_kunitz.fasta | tail -n 2 >> kunitz_representatives.fasta; done`
8) Subsequently check if there are sequences with a lenght that is not between 45 and 80 with the command:  
`awk 'NR%2==1 {id=$0} NR%2==0 {len=length($0); if (len < 45 || len > 80) {print id , len}}' kunitz_representatives.fasta`  
it appears that there are three sequences: >2ODY_E 127 >5JBT_C 38 >5NX1_D 81. Since the last two are very close to the desired range, only the first sequence will be removed 
9) Remove the sequence 2ODY_F using the command:  
`awk '{if ($0 == ">2ODY_F") {skip=1} else if (skip == 1) {skip=0; next} else {print $0}}' kunitz_clustered.clst > kunitz_msa_ready.fasta`
10) checking the number of sequences left with the command:  
`command grep ">" kunitz_msa_ready.fasta | wc`  
The output is 24 structures.
11) Subsequently run PDBeFOLD trough the PDBeFOLD web server to obtain our Multiple Structural Alignement. A list containing the pdb ids, with the chain identifier at the end of the ids preceded by a semicolon is needed. To obtain it, run the command:  
`awk 'substr($0,1,1) == ">" {id = substr($0, 2) split(id, a, "_") print a[1] ":" a[2]}' kunitz_msa_ready.fasta > kunitz_ids.txt`
12) By looking at the output report, the protein 5JBT has an RMSD value of 2.9. That is a very high RMSD compared to that of the other proteins that is never above 1 A. We can therefore rerun the alignment without that protein by manually removing it from the id list.
13) After downloading the report, the next step is to process it to obtain a fasta file without headers and lower case letters. We can use the command:  
`awk '{if (substr($1,1,1)==">") {print "\n"toupper($1)} else {printf "%s",toupper($1)}}' pdbe_fold_output.ali | sed s/PDB:// > kunitz_hmm_ready.fasta`
14) Subsequently it is possible to run HMMBUILD to train a Kunitz specific HMM. 
15) Run hmmbuilt with the command:  
`hmmbuild kunitz_domain.hmm kunitz_hmm_ready.fasta`
16) Download all the kunitz annotated proteins (according to PFAM) from Uniprot Swissprot as well as all the not kunitz proteins with the uniprot queries:   
`ALL PROTEINS THAT ARE NOT KUNITZ > (NOT (xref:pfam-PF00014)) AND (reviewed:true)`
`ALL KUNITZ PROTEINS > (xref:pfam-PF00014) AND (reviewed:true)`
17) Clean the two datasets to get rid of the superfluous header information with the command:  
`awk 'substr($0,1,1)==">"{split($0,a,"|"); print ">"a[2]; next}{print}'`
18) Subsequently, with a python script (get_uniprot.py), it was got the cross references between the Pbd structures and Uniprot Swissprot, with the aim of removing the sequences that will be used in HMMBUILD from the Kunitz Swissprot dataset. Uniprot ids linked to the Pdb entries have been put in a text file.
19) Upon inspecting the file, it was noticed many redundant ids, so it was removed them using the command:  
`sort uniprot_ids_to_rm.txt | uniq -i > unique_ids_to_rm.txt`
20) Remove from the ramaining sequences from Kunitz Swissprot dataset using a python script (sequence_remover.py). By adding a counter to the proteins that were being removed, it was can see that 10 proteins sequences were not removed, but this was expected. Some of the protein Ids that were obtained using the get_uniprot.py script are not Kunitz proteins, and this is because when we obtained our uniprot ids thanks to the get_uniprot.py script, we also obtained ids of proteins forming complexes with the Kunitz proteins, that were not necessairly Kunitz.
21) Extract IDs from the Swissprot Not kunitz dataset and the Swissprot Kunitz dataset (with the sequences used for training removed) with the command:  
`grep ">" DATASET_not_kunitz.fasta > ID_negatives.id`
`grep ">" DATASET_all_kunitz_not_training.fasta > ID_positives.id`
22) Generate random permutation of those ids with the command:  
`sort -R ID_negatives.id > ID_negatives.random`
`sort -R ID_positives.id > ID_positives.random`
23) Divide the datasets in 2 for the two fold cross validation, but first count the number of entries with the command:  
`grep ">" ID_positives.random | wc;`
`grep ">" ID_negatives.random | wc`
24) Obtain the two halves of each dataset for 2 fold cross validation with the commands:  
`head -n 191 ID_positives.random > 1_ID_positivies.random;`
`tail -n 191 ID_positives.random > 2_ID_positivies.random;`
`head -n 286416 ID_negatives.random > 1_ID_negatives.random;`
`tail -n 286416 ID_negatives.random > 2_ID_negatives.random`
25) Create the two halved random datasets with the python script get_sequence.py. Then run the following commands to obtain the two fasta datasets:  
`for file in *_ID_positivies.random; do echo $file; python3 get_sequence.py $file DATASET_all_kunitz_not_training.fasta; done`
`for file in *_ID_negatives.random; do echo $file; python3 get_sequence.py $file DATASET_not_kunitz.fasta; done`
26) Having obtained all datasets needed, run the hmmsearch with the flags:  
`hmmsearch --tblout --max -Z 1000.`  
With this options heuristics intrinsic to hmmsearch are excluded, and with the -Z 1000 it is assumed that in each dataset we have 1000 entries, in this way we can compare the e-value between datasets of different sizes. With the last flag, the output is returned in a tabular format.   
`hmmsearch --max -Z 1000 --tblout 1_positives.out kunitz_domain.hmm 1_positives.fasta`
`hmmsearch --max -Z 1000 --tblout 1_negatives.out kunitz_domain.hmm 1_negatives.fasta`
27) Create the class files containing the id, the e-value and the class (positive, 1 or negative, 0 ) with the command:  
`grep -v "^#" 1_positives.out | awk '{print $1 , 1 , $5}' >1_positives.class;`
`grep -v "^#" 1_negatives.out | awk '{print $1 , 0 , $5}' >1_negatives.class`  
To make sure all positives and all negatives were obtained, run the command:  
`awk '{print $1}' 1_positives.class | sort -u | wc;`
`awk '{print $1}' 1_negatives.class | sort -u | wc`  
In the class file we have all the matches for the positive dataset, while for the negative dataset we only have around two thousand matches. This is because the e-value threshold set by hmmer is 10, and most of the sequences in the negative dataset, since they are not Kunitz, have an e-value higher than the treshold, and the program doesn't return them in the output. To reintroduce the missing ids we can run this command for the negative class files:
`comm -23 <(awk '{split($0, a, ">"); print a[2]}' 1_ID_negatives.random | sort) <(cut -f1 1_negatives.class | sort) | awk '{print $1" 0 10"}' >> 1_negatives.class` 
28) Merge the two classes (positive and negative) in a single file with the command:  
`cat 1_negatives.class 1_positives.class > 1_merged.class;`
29) Assess the performance using the e-value of the entire sequence. To do this, it was uses the performance.py python script. To select the best threshold, run the command:  
`for i in $(seq 1 13); do python3 performance.py 1_merged.class 1e-$i 1 >> 1_performance_output.txt ; done`
`for the 1_merged.class file, the best performance in terms of MCC is achived with threshold 1e-6. By looking at the confusion matrix`  
we can see that this treshold gives us perfect true-positive-rate and almost perfect precision. We end up with only 2 false negatives.
30) By performing the same task with the second class file, obtained with the same procedure as the first, we can see that the best performance in term of MCC is achived again with thershold 1e-6. Merging the two files and running the command:  
`for i in $(seq 1 13); do python3 performance.py <(cat 2_merged.class 1_merged.class) 1e-$i 1 >> merged_performance_output.txt`    
4 false negatives are obtained, as expected, with the treshold 1e-6.  
32) The 4 false negatives were identified with the command:        
`sort -grk 3 <(cat 1_positives.class 2_positives.class) > sorted_positives.class ; less sorted_positives.class`     
This are the entries that are currently considered false negatives:
D3GGZ8 1 0.002  
O62247 1 0.00013  
A0A1Q1NL17 1 1.6e-05  
Q8WPG5 1 4.1e-06  
Inspecting the merged_performance_output.txt file, appears clear that by using a treshold in the order of e-04 or higher will lead to an increase of the number of false positives, and a lower overall performance performance as marked by the MCC. A treshold between 1e-05 and 1e-06 also cannot lead to a better performance, because we would inevitably incorporate some false postivies. In fact, by running the command:  
`for i in $(seq 1 10); do python3 performance.py <(cat 2_merged.class 1_merged.class) ${i}e-6 1; echo --------------------; done`    
The confusion matrix stays the same until the value 5e-06 where we finally reduce by one the number of false negatives, but we also increase by one the number of false positives.  
33) By running the command:  
`for i in $(seq 1 10); do python3 performance.py <(cat 2_merged.class 1_merged.class) ${i}e-5 1; echo --------------------; done`  
That is, testing the model threshold with value between 1e-5 and 1e-4 we achive the best possible results for the model with the treshold 2e-5 and 1 false positive, 2 false negatives, MCC= 0.9960664091981688. A treshold of 3e-5 leads to the incorporation of 1 more false positive, and the number dramatically increases as we approach the treshold of e-4. Inspecting the false negatives with the intent of identofying the false positive entry with the command:  
`sort -gk 3 <(cat 1_negatives.class 2_negatives.class) > sorted_negatives.class ; less sorted_negatives.class`  
It is revealed that the only false pasitive with the treshold of 2e-5 is the protein:  
P84555 0 3.3e-06  
By analisying its Uniprot entry, this protein is annotated as a Kunitz proteins, however it is not annotated by PFAM, but by the Interpro database. Upon further investigation, it was found that the proteins:  
P84555   
P0DJ63   
P56409   
P85039   
P83605  
Q09JW4  
Are not annotated by PFAM as Kunitz proteins, however they are annotated by Interpro as such. This proteis have the lowest e-value among the negatives.   
34) Considering this findings, It was wanted to verify if using the Interpro annotation instead of the PFAM one leads to better results. To decide if this could be a viable option, It was queried the Uniprot database:  
the query: (xref:pfam-PF00014) AND (reviewed:true) found 398 <-- proteins annotated as Kunitz by PFAM    
the query: (xref:pfam-PF00014) AND (xref:interpro-IPR036880) AND (reviewed:true) found 398 results <-- proteins that are annotated as Kunitz by PFAM and Interpro.    
the query: ((xref:interpro-IPR036880) OR (xref:pfam-PF00014)) AND (reviewed:true) found 409 results. <-- proteins annotated as Kunitz by Interpro or PFAM      
We can deduct that all PFAM annotated proteins are also Interpro annotated proteins, but not viceversa. For this specific protein family it is better to use the Interpro annotation to incorporate as many Kunitz as possible and not have a biased result.  
35) Instead of starting from scartch, it was faster to look for the 11 missing Kunitz proteins in the negative dataset. By manually checking for the entries with the lowest e-value among the negatives, it was found that, unsurprisingly, all of them where Interpro Kunitz. 
36) The Interpro only annotated positives were obtained with the command:  
`head -n 11 sorted_negatives.class | awk '{print ">" $1}' > interpro_positives.txt`  
The 11 interpro kunitz were put in a text file, and also added the ">" symbol to it.
37) Subsequently those ids were removed from the file containing the randomly shuffled negative ids using the command:  
`comm -23 <(sort ID_negatives.random) <(sort interpro_positives.txt) > definitive_negatives.id`  
And added the 11 proteins it the positive dataset with the command:  
`cat ID_positives.id interpro_positives.txt > definitive_positives.id`  
38) Having obtained the updated datasets, it is time to run the two fold cross validation exactly as before. Start by shuffling randomically the definitive datasets:  
`sort -R definitive_negatives.id > definitive_negatives.random ;`  
`sort -R definitive_positives.id > definitive_positives.random`
39) Subsequently it was create the datasets for the two fold cross validation:  
`head -n 197 definitive_positives.random > 1_definitive_ID_positivies.random ;`  
`tail -n 196 definitive_positives.random > 2_definitive_ID_positivies.random ;`  
`head -n 286410 definitive_negatives.random > 1_definitive_ID_negatives.random ;`  
`tail -n 286411 definitive_negatives.random > 2_definitive_ID_negatives.random ;`  
40) Having obtained the missing ids, get the sequences using the get_sequence python script. First, merge the dataset containing the Kunitz proteins not used for training with the dataset of not Kunitz proteins, since the 11 Interpro Kunitz appear in the negative dataset.  
`cat DATASET_all_kunitz_not_training.fasta DATASET_not_kunitz.fasta > DATASET_swissprot_not_training.fasta`  
and then run the following commands:  
`python3 get_sequence.py 2_definitive_ID_positivies.random DATASET_swissprot_not_training.fasta;`  
`python3 get_sequence.py 1_definitive_ID_positivies.random DATASET_swissprot_not_training.fasta;  `
`python3 get_sequence.py 1_definitive_ID_negatives.random DATASET_swissprot_not_training.fasta;`  
`python3 get_sequence.py 2_definitive_ID_negatives.random DATASET_swissprot_not_training.fasta;`
41) Subsequently run the performance script and evaluate the model with the corrected datasets. First run hmmsearch.  
`hmmsearch --max -Z 1000 --tblout 2_definitive_positives.out kunitz_domain.hmm 2_definitive_positives.fasta;`  
`hmmsearch --max -Z 1000 --tblout 1_definitive_positives.out kunitz_domain.hmm 1_definitive_positives.fasta;`  
`hmmsearch --max -Z 1000 --tblout 2_definitive_negatives.out kunitz_domain.hmm 2_definitive_negatives.fasta;`  
`hmmsearch --max -Z 1000 --tblout 1_definitive_negatives.out kunitz_domain.hmm 1_definitive_negatives.fasta;`
42) Subsequently create the class files:  
`grep -v "^#" 1_definitive_positives.out | awk '{print $1 , 1 , $5}' >1_definitive_positives.class ;`  
`grep -v "^#" 1_definitive_negatives.out | awk '{print $1 , 0 , $5}' >1_definitive_negatives.class`  
and incorporate the missing entries:  
`comm -23 <(awk '{split($0, a, ">"); print a[2]}' 2_definitive_ID_negatives.random | sort) <(cut -f1 2_definitive_negatives.class | sort) | awk '{print $1" 0 10"}' >> 2_definitive_negatives.class;`  
`comm -23 <(awk '{split($0, a, ">"); print a[2]}' 1_definitive_ID_negatives.random | sort) <(cut -f1 1_definitive_negatives.class | sort) | awk '{print $1" 0 10"}' >> 1_definitive_negatives.class`
43) Merge the positive and negative classes:  
`cat 1_definitive_negatives.class 1_definitive_positives.class > 1_definitive_merged.class;`  
`cat 2_definitive_negatives.class 2_definitive_positives.class > 2_definitive_merged.class`
44) By running the following command:  
`for i in $(seq 1 13); do python3 performance.py 1_definitive_merged.class 1e-$i 1 >> 1_definitive_performance_output.txt ; done`  
and inspecting the 1_definitive_performance_output.txt it was get a perfect confusion matrix with the treshold 0.001 0 false positives, 0 false negatives and an MCC of 1. By running the same command with the second dataset it was obtained 1 false negative and 1 false positive, with the 0.001 threshold,  MCC= 0.9948944952004392. This is the best MCC and confusion matrix for this dataset. Having obtained the best order of magnitude for the threshold, fine tune the model to try to improve the perfomance even more:  
`for i in $(seq 1 10); do python3 performance.py <(cat 2_definitive_merged.class 1_definitive_merged.class) ${i}e-3 1; echo --------------------; done`  
the best performance is achived with a treshold of 0.002 with an MCC= 0.9987292933109377 and one single false positive. This is coherent with the results obtained with the previous datasets used for assessing the performance, the ones where the 11 sequences interpro Kunitz were considered false positives. In fact, the confusion matrix for the 0.001 treshold showed 11 false positives, that were in reality actual positives.   
45) Inspect the false positive protein with the command:  
`sort -grk 3 <(cat 1_definitive_negative.class 2_definitive_negative.class) > sorted_definitive_negatives.class ; tail -n 1 sorted_definitive_negatives.class`  
The false positive protein is the uniprot entry  
C0HMD5  
By analizying the uniprot entry, again, it again appears to be a case of actual positive among the neagitves,because this entry is manually annotated as Kunitz protein. however it is annotated by Prosite alone. By looking at the other proteins that exibit a low e-value in the negative dataset, in particular the other 10 entries with the lowest e-value, there where no other Kunitz proteins, suggesting this was the only case of Prosite Kunitz in the negative dataset. By removing the entry C0HMD5 from the negatives and putting it in the positives it was obtained a model that with the threshold 0.002 can achive an MCC = 1 and 0 false positive and 0 false negatives.
