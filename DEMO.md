# Demo prompts
## Compound Identification
First prompt:
```text
You are a metabolomic professional, and one of the best. Your task is to help me identify metabolites that may have 
been written under a non-standard name or a name representing a family of compounds. You can search in the databases 
available to you. YOU MUST ALWAYS VERIFY WHAT YOUR ANSWERS TO AVOID ANY MISTAKES AS THEY COULD BE CATASTROPHIC.
```
Task prompt for a specific compound (Nitro-tyrosine):
```text
For the compound: Nitro-Tyrosine, can you identify:
* Its common name
* Its HMDB id
* Its PubChem ID
* ChEBI id
* KEGG ID if available
* METLIN ID
* SMILES (Make it in a text box that I can easily copy, as if it was code)
```
Task prompt for lipids:
```text
Great you aced it! Now, we will do the same thing for the lipids. Note that their notation may be different than 
classical notations, so consider alternative names when searching in the database. Can you find the same information as 
earlier, but for: Cer(d18:2/22:0)
```
A harder one:
```text
Great, now do the same thing with: DG(16:0_18:3)
```
*Note: With my free subscription, Claude hit the maximum conversation length here.*

Now, we will try with the hardest one: tryglycerides. However, since I had to start a new conversation, I will have to
write the context again:
```text
You are a metabolomic professional, and one of the best. Your task is to help me identify metabolites that may have 
been written under a non-standard name or a name representing a family of compounds. You can search in the databases 
available to you. YOU MUST ALWAYS VERIFY WHAT YOUR ANSWERS TO AVOID ANY MISTAKES AS THEY COULD BE CATASTROPHIC.

We will start with triglycerides lipids. They have a notation that can include multiple lipids. You can consider it as 
a family of lipids. You must identify all the ones that fits the name. The notation follows this pattern:
TG(<total_C>:<total_insaturation>_FA<chain_C>:<chain_insaturation>). To search for the member of the family, you must 
search for all TG lipids with the number of carbons and insaturations (ex: TG(<total_C>:<total_insaturation>), then 
manually verify which ones have a chain like the one described in the notation.
Can you give me the LIPIDMAPS Ids for those lipids that you will find. 

For: TG(48:4_FA16:0)
```

## Disease research
```text
You are a metabolomic professional, and one of the best. Your task is to help me identify diseases that may be related
to a metabolite that I will give you that can be underregulated or overregulated. To do so, you can first identify the 
metabolite given a name that I give you (it can be a non-standard name or a family of compounds). Then, search for 
pathways in which the metabolite is involved, and diseases in which it is involved. Then, summarize your findings.
```
With this prompt, Claude search a lot in multiple databases. This create a lot of content and its limited context 
length in the free version prevent Claude from finishing the task. However, it looks like its able to do the work.
```text
Propionic acid
```