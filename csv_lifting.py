from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
import pandas as pd

g = Graph()

# Declaring namespaces
ex = Namespace("http://example.org/")
mo = Namespace("http://www.movieontology.org/2009/11/09/movieontology.owl#")
dbo = Namespace("http://dbpedia.org/ontology/")
dbr = Namespace("http://dbpedia.org/resource/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
dct = Namespace("http://purl.org/dc/terms/")
foaf = Namespace("http://xmlns.com/foaf/0.1/")


# Binding namespaces' associated prefixes to graph
g.bind("ex",ex)
g.bind("mo", mo)
g.bind("dbo",dbo)
g.bind("dbr",dbr)
g.bind("dc", dc)
g.bind("dct",dct)
g.bind("foaf", foaf)


# Load the CSV data as a pandas Dataframe.
df = pd.read_csv(r'static/csv/IMDB-Movie-Data.csv')

# Splitting actor names into their own columns
df[["Actor1","Actor2", "Actor3","Actor4"]] = df.Actors.str.split(',',expand = True)
df = df.drop(['Actors'], axis=1)
# Making all df values into string for RDF triples
df = df.applymap(str)

#Making new columns witout underscores, saved for the Literals later. 
df['Title_clean'] = df['Title']
df['Director_clean'] = df['Director']
df['Actor1_clean'] = df['Actor1']
df['Actor2_clean'] = df['Actor2']
df['Actor3_clean'] = df['Actor3']
df['Actor4_clean'] = df['Actor4']

# Replace spaces with "_" so that URI's become valid.
df['Title'] = df['Title'].replace(to_replace=" ", value="_", regex=True)
df['Director'] = df['Director'].replace(to_replace=" ", value="_", regex=True)
df['Actor1'] = df['Actor1'].replace(to_replace=" ", value="_", regex=True)
df['Actor2'] = df['Actor2'].replace(to_replace=" ", value="_", regex=True)
df['Actor3'] = df['Actor3'].replace(to_replace=" ", value="_", regex=True)
df['Actor4'] = df['Actor4'].replace(to_replace=" ", value="_", regex=True)

#Replace comma with "-"
df['Genre'] = df['Genre'].replace(to_replace=",", value="-", regex=True)

# Some Actor names started with space - Removing " " from actor names starting with " " and "_"
for col in df.columns:
    df[col] = df[col].apply(lambda x : x[1:] if x.startswith(" ") else x)
    df[col] = df[col].apply(lambda x : x[1:] if x.startswith("_") else x)

#Looping through the CSV data, and then make RDF triples.
for index, row in df.iterrows():
    # Selecting row for subject
    subject = row['Title']
    # Create triples: e.g. "subject - hasActor - "Daniel Radcliffe"
    # Also adding XSD to define datatypes
    g.add((URIRef(ex + subject), URIRef(mo + "title"), Literal(row["Title_clean"], datatype=XSD.string)))
    g.add((URIRef(ex + subject), URIRef(dbo + "genre"), Literal(row["Genre"], lang='en')))
    g.add((URIRef(ex + subject), URIRef(mo + "hasDirector"), URIRef(ex + row["Director"])))
    g.add((URIRef(ex + subject), URIRef(mo + "hasActor"),  URIRef(ex + row["Actor1"])))
    g.add((URIRef(ex + subject), URIRef(mo + "hasActor"), URIRef(ex + row["Actor2"])))
    g.add((URIRef(ex + subject), URIRef(mo + "hasActor"), URIRef(ex + row["Actor3"])))
    g.add((URIRef(ex + subject), URIRef(mo + "hasActor"), URIRef(ex + row["Actor4"])))
    g.add((URIRef(ex + subject), URIRef(dbo + "rating"), Literal(row["Rating"], datatype=XSD.float)))
    # Using dublin core(dc) to describe the subject's description, as dbo was lacking.
    g.add((URIRef(ex + subject), URIRef(dc + "description"), Literal(row["Description"], lang='en')))
    g.add((URIRef(ex + subject), URIRef(dct + "created"), Literal(row["Year"], datatype=XSD.int)))
    g.add((URIRef(ex + subject), URIRef(mo + "runtime"), Literal(row["Runtime (Minutes)"], datatype=XSD.int)))
    # Adding RDF type to subject
    g.add((URIRef(ex + subject), RDF.type, mo.Movie))
    
    # Adding director resources to graph
    director = row['Director']
    # Movieontology uses dbr uri for director
    g.add((URIRef(ex + director), RDF.type, dbr.Film_Director))
    g.add((URIRef(ex + director), URIRef(foaf + "name"), Literal(row["Director_clean"])))
    # isDirectorOf is inverse of the movies' hasDirector  
    g.add((URIRef(ex + director), URIRef(mo + "isDirectorOf"), URIRef(ex + row["Title"])))
    
    # Adding actor resources to graph
    actor1 = row['Actor1']
    g.add((URIRef(ex + actor1), RDF.type, dbo.Actor))
    g.add((URIRef(ex + actor1), URIRef(foaf + "name"), Literal(row["Actor1_clean"])))
    g.add((URIRef(ex + actor1), URIRef(mo + "isActorIn"), URIRef(ex + row["Title"])))
    
    actor2 = row['Actor2']
    g.add((URIRef(ex + actor2), RDF.type, dbo.Actor))
    g.add((URIRef(ex + actor2), URIRef(foaf + "name"), Literal(row["Actor2_clean"])))
    g.add((URIRef(ex + actor2), URIRef(mo + "isActorIn"), URIRef(ex + row["Title"])))
    
    actor3 = row['Actor3']
    g.add((URIRef(ex + actor3), RDF.type, dbo.Actor))
    g.add((URIRef(ex + actor3), URIRef(foaf + "name"), Literal(row["Actor3_clean"])))
    g.add((URIRef(ex + actor3), URIRef(mo + "isActorIn"), URIRef(ex + row["Title"])))
    
    actor4 = row['Actor4']
    g.add((URIRef(ex + actor4), RDF.type, dbo.Actor))
    g.add((URIRef(ex + actor4), URIRef(foaf + "name"), Literal(row["Actor4_clean"])))
    g.add((URIRef(ex + actor4), URIRef(mo + "isActorIn"), URIRef(ex + row["Title"])))

## Serializing graph to a file in turtle format 
#g.serialize(destination="static/rdf/moviedata_turtle", format="ttl")

