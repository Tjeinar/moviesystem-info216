from flask import Flask, request, render_template, url_for, redirect, session
from rdflib import Graph, Literal, Namespace, URIRef, XSD
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

g.parse('static/rdf/moviedata_turtle4',format='turtle')

####################
## SPARQL queries ##
####################
def movie_details(title):
    user_title = title
    res = g.query("""SELECT DISTINCT ?title ?rating ?year ?director ?genre
                    WHERE {
                    ?movie a mo:Movie .
                    ?movie mo:title ?title .
                    ?movie mo:title '"""+user_title+"""'^^xsd:string .
                    ?movie dbo:rating ?rating .
                    ?movie dct:created ?year .
                    ?movie mo:hasDirector ?director .
                    ?movie dbo:genre ?genre
                    }
                    """)
    return list(res)

#Query looking for all actor names, ordered alphabetically.
def alldirectors_query():
    res = g.query("""SELECT DISTINCT ?name
                    WHERE {
                    ?director a dbr:Film_Director .
                    ?director foaf:name ?name
                    }
                    ORDER BY ASC(?name)
                    """)
    return list(res)

#Query looking for all movie titles, ordered alphabetically.
def alltitles_query():
    res = g.query("""SELECT DISTINCT ?title 
                     WHERE {
                     ?movie a mo:Movie .
                     ?movie mo:title ?title 
                     }
                     ORDER BY ASC(?title)
                     """)
    return list(res)

# Query looking for all actor names, ordered alphabetically. 
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
    res = g.query("""SELECT DISTINCT ?title ?director ?name ?rating
                     WHERE {
                     ?title a mo:Movie .
                     ?title mo:hasDirector ?director .
                     ?title mo:hasDirector '"""+user_director+"""' .
                     ?title mo:title ?name .
                     ?title dbo:rating ?rating .
                     FILTER (?rating >= '"""+user_rating+"""'^^xsd:float) 
                     }
                     ORDER BY DESC(?rating)
                     """) 
    return list(res)

def reccomendation_query(actor1,actor2,actor3):
    user_actor_choice1 = actor1
    user_actor_choice2 = actor2
    user_actor_choice2 = actor3
    res = g.query("""SELECT DISTINCT ?title ?rating ?genre ?description ?director (GROUP_CONCAT(distinct ?actor; separator = ", ") as ?actors)
                    WHERE {
                    ?movie mo:title ?title .  
                    ?movie dbo:rating ?rating .
                    ?movie dbo:genre ?genre .
                    ?movie dc:description ?description .
                    ?movie mo:hasDirector ?director .
                    {
                        ?movie mo:hasActor ?actor .
                        ?movie mo:hasActor '"""+actor1+"""'
                    }
                    UNION
                    {
                        ?movie mo:hasActor ?actor .
                        ?movie mo:hasActor '"""+actor2+"""'
                    }
                    FILTER(?rating >= "1"^^xsd:int)
                    }
                    GROUP BY ?title ?rating ?genre ?description ?director
                    LIMIT 3
                    """)
    return list(res)        
    
###################
### App routing ###
###################

@app.route('/')
def enter():
    return redirect(url_for("home"))

@app.route('/home', methods=['GET','POST'])
def home():
    return render_template('index.html')

@app.route("/database",methods=["GET", "POST"])
def database():
    session["MOVIETITLE"] = None
    if request.method == "POST":
        movietitle = request.form.get("movietitle")

        session["MOVIETITLE"] = movietitle
        return render_template("database.html",alltitles=alltitles_query(),result=movie_details(session["MOVIETITLE"]),check=session["MOVIETITLE"] )

    return render_template("database.html",alltitles=alltitles_query(), details=movie_details(" "))



@app.route("/actorsearch",methods=["GET", "POST"])
def actorsearch():

    # Getting input from user's favourite actors
    if request.method == "POST":
        choice1 = request.form.get("actornames")
        choice2 = request.form.get("actornames2")
        choice3 = request.form.get("actornames3")
        choice4 = request.form.get("actornames4")

        session["ACTORCHOICE1"] = choice1
        session["ACTORCHOICE2"] = choice2
        session["ACTORCHOICE3"] = choice3
        session["ACTORCHOICE4"] = choice4
        return redirect(url_for("actorsearchresult"))

    return render_template("actorsearch.html", allactors=allactors_query())

@app.route("/actorsearch/result", methods=["GET", "POST"])
def actorsearchresult():
    # Using input from session cookie
    choice1 = session.get("ACTORCHOICE1")
    choice2 = session.get("ACTORCHOICE2")
    choice3 = session.get("ACTORCHOICE3")
    choice4 = session.get("ACTORCHOICE4")

    return render_template("actorsearchresult.html",reccomendation=reccomendation_query(choice1,choice2,choice3))


@app.route("/directorsearch", methods=["GET", "POST"])
def search():

    # Getting form data entered by user in search field
    if request.method == "POST":
        director = request.form.get("directorname")
        rating = request.form.get("rating")
    
        ## Storing user input data into session cookie
        session["DIRECTORNAME"] = director 
        session["RATING"] = rating
        #print(session)
        return redirect(url_for('directorsearchresult'))

    return render_template("directorsearch.html",title="Search", directors = alldirectors_query())




@app.route('/directorsearch/result',methods=['GET','POST'])
def directorsearchresult():
   
    directorname = session.get("DIRECTORNAME")
    ratingreq = session.get("RATING")
    return render_template('directorsearchresult.html',title='Result',specific=specific_query(ratingreq,directorname))
  

 

if __name__ == "__main__":
    app.run(debug=True)



