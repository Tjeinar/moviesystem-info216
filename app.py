from flask import Flask, request, render_template, url_for, redirect, session
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, FOAF, RDFS, OWL, XSD
from rdflib.plugins.sparql import prepareQuery
import datetime 

app = Flask(__name__)

app.config['SECRET_KEY'] = "1337"


g = Graph()

# Declaring namespaces
ex = Namespace("http://example.org/")
mo = Namespace("http://www.movieontology.org/2009/11/09/movieontology.owl#")
dbo = Namespace("http://dbpedia.org/ontology/")
dbr = Namespace("http://dbpedia.org/resource/")
dc = Namespace("http://purl.org/dc/elements/1.1/")
dct = Namespace("http://purl.org/dc/terms/")

# Binding namespaces' prefixes to graph
g.bind("ex",ex)
g.bind("dbo",dbo)
g.bind("dbr",dbr)
g.bind("mo", mo)
g.bind("foaf", FOAF)
g.bind("dc", dc)
g.bind("dct",dct)


# Parsing RDF data to graph. 
g.parse('static/rdf/moviedata_turtle',format='turtle')

# List of all the individual movie genre names. 
genreoptions = ['Action','Adventure','Biography', 'Comedy','Crime','Drama','Family', 'Fantasy','History', 'Horror','Music','Mystery','Romance','Sci-Fi','Sport','Thriller','War','Western'] 


######################
### SPARQL queries ###
######################

# Query returning the details about a specific movie title. 
def movie_details(title):
    user_title = title
    res = g.query("""SELECT DISTINCT ?title ?rating ?year ?description ?directorname ?genre (GROUP_CONCAT(DISTINCT ?actorname; separator = ", ") AS ?actors)
                    WHERE {
                    ?movie a mo:Movie .
                    ?movie mo:title ?title .
                    ?movie mo:title '"""+user_title+"""'^^xsd:string . 
                    ?movie dbo:rating ?rating .
                    ?movie dc:description ?description .
                    ?movie dct:created ?year .
                    ?movie dbo:genre ?genre .
                    ?movie mo:hasActor ?actor .
                    ?movie mo:hasDirector ?director .
                    ?director foaf:name ?directorname .
                    ?actor foaf:name ?actorname
                    }
                    GROUP BY ?title ?rating ?year ?directorname ?genre
                    """)
    return list(res)

#Query looking for all director names, ordered alphabetically.
def alldirectors_query():
    res = g.query("""SELECT DISTINCT ?name
                    WHERE {
                    ?movie a mo:Movie .
                    ?movie mo:hasDirector ?director .
                    ?director foaf:name ?name
                    }
                    ORDER BY ASC(?name)
                    """)
    return list(res)

#Query returning all movie titles, ordered alphabetically.
def alltitles_query():
    res = g.query("""SELECT DISTINCT ?title 
                     WHERE {
                     ?movie a mo:Movie .
                     ?movie mo:title ?title 
                     }
                     ORDER BY ASC(?title)
                     """)
    return list(res)

# Query returning all actor names, ordered alphabetically. 
def allactors_query():
    res = g.query("""SELECT DISTINCT ?name
                     WHERE {
                     ?actor a dbo:Actor .
                     ?actor foaf:name ?name 
                     }
                     ORDER BY ASC(?name)
                     """)
    return list(res)
  

# Query that finds all movies directed by specific director, ordered by highest rating. 
def specific_query(rating,director):
    user_rating = rating
    user_director = director
    res = g.query("""SELECT DISTINCT ?title ?name ?rating
                     WHERE {
                     ?movie a mo:Movie .
                     ?movie mo:title ?title .
                     ?movie dbo:rating ?rating .
                     ?movie mo:hasDirector ?director .
                     ?director foaf:name ?name .
                     ?director foaf:name '"""+user_director+"""' .
                     FILTER (?rating >= '"""+user_rating+"""'^^xsd:float) 
                     }
                     ORDER BY DESC(?rating)
                     """) 
    return list(res)

# Query that takes in 3 actor names, 2 genres - and returns the top rated movies based on rating. Limited by max 3 results. 
def reccomendation_query(actor1,actor2,actor3,genre1,genre2):
    user_actor_choice1 = actor1
    user_actor_choice2 = actor2
    user_actor_choice3 = actor3

    user_genre_choice1 = genre1
    user_genre_choice2 = genre2
    res = g.query("""SELECT DISTINCT ?title ?rating ?genre ?year ?description ?directorname ?actorname
                    WHERE {
                    ?movie mo:title ?title .  
                    ?movie dbo:rating ?rating .
                    ?movie dbo:genre ?genre .
                    ?movie dct:created ?year .
                    ?movie dc:description ?description .
                    ?movie mo:hasDirector ?director .
                    ?director foaf:name ?directorname .
                    ?movie mo:hasActor ?actor .
                    ?actor foaf:name ?actorname .
                    {
                        ?actor foaf:name '"""+actor1+"""'
                    }
                    UNION
                    {
                        ?actor foaf:name '"""+actor2+"""'
                    }
                    UNION
                    {
                        ?actor foaf:name '"""+actor3+"""' 
                    }
                    FILTER (contains(?genre, '"""+genre1+"""'@en ) || contains(?genre, '"""+genre2+"""'@en ))
                    }
                    ORDER BY DESC(?rating)
                    LIMIT 3
                    """)
    return list(res)        
    
###################
### App routing ###
###################

# Here we are defining various routes for the app(URLs) and rendering templates, passing sparql results as lists into variables. 

@app.route('/')
def enter():
    return redirect(url_for("home"))

@app.route('/home', methods=['GET','POST'])
def home():
    return render_template('index.html')

@app.route("/database",methods=["GET", "POST"])
def database():
    session["MOVIETITLE"] = None

    # Getting form data entered by user in search field
    if request.method == "POST":
        movietitle = request.form.get("movietitle")

        # Storing user input data in session cookie
        session["MOVIETITLE"] = movietitle
        return render_template("database.html",alltitles=alltitles_query(),result=movie_details(session["MOVIETITLE"]),check=session["MOVIETITLE"] )

    return render_template("database.html",alltitles=alltitles_query(), details=movie_details(" "))



@app.route("/actorsearch",methods=["GET", "POST"])
def actorsearch():

    # Getting input from user's favourite actors and genres
    if request.method == "POST":
        choice1 = request.form.get("actornames")
        choice2 = request.form.get("actornames2")
        choice3 = request.form.get("actornames3")
        choice4 = request.form.get("genreoptions")
        choice5 = request.form.get("genreoptions2")

        session["ACTORCHOICE1"] = choice1
        session["ACTORCHOICE2"] = choice2
        session["ACTORCHOICE3"] = choice3
        session["GENRECHOICE1"] = choice4
        session["GENRECHOICE2"] = choice5
        return redirect(url_for("actorsearchresult"))

    # Passing list of results from allactors_query() to a variable called allactors
    return render_template("actorsearch.html", allactors=allactors_query(), genreoptions=genreoptions)

@app.route("/actorsearch/result", methods=["GET", "POST"])
def actorsearchresult():
    # Using input stored in the session cookie 
    choice1 = session.get("ACTORCHOICE1")
    choice2 = session.get("ACTORCHOICE2")
    choice3 = session.get("ACTORCHOICE3")
    choice4 = session.get("GENRECHOICE1")
    choice5 = session.get("GENRECHOICE2")

    return render_template("actorsearchresult.html",reccomendation=reccomendation_query(choice1,choice2,choice3,choice4,choice5))


@app.route("/directorsearch", methods=["GET", "POST"])
def search():

    # Getting form data entered by user in search field
    if request.method == "POST":
        director = request.form.get("directorname")
        rating = request.form.get("rating")
    
        ## Storing user input data into session cookie
        session["DIRECTORNAME"] = director 
        session["RATING"] = rating
      
        return redirect(url_for('directorsearchresult'))

    return render_template("directorsearch.html",title="Search", directors = alldirectors_query())

@app.route('/directorsearch/result',methods=['GET','POST'])
def directorsearchresult():
   
    directorname = session.get("DIRECTORNAME")
    ratingreq = session.get("RATING")
    return render_template('directorsearchresult.html',title='Result',specific=specific_query(ratingreq,directorname))

# RDF grapher; visualization of our RDF graph
@app.route('/rdfgraph')
def extra():
    return render_template('graph.html')  

if __name__ == "__main__":
    app.run(debug=True)



