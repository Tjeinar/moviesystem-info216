# Queries that were used f.ex for the project report, but not included in the web application.


# Counting instances of actor class - count returned is 1986. 
def actor_type():
    res = g.query("""SELECT (COUNT(*) AS ?count)
                     WHERE {
                        ?subject a dbo:Actor
                     }
                     """) 
    return list(res)

# Counting instances of director class - count returned is 644. 
def director_type():
    res = g.query("""SELECT (COUNT(*) AS ?count)
                     WHERE {
                        ?subject a dbo:Actor
                     }
                     """) 
    return list(res)


# Query to find out how many subjects are both of type actor and film_director. In this data set the count is 36. 
def actor_and_director_type():
    res = g.query("""SELECT (COUNT(*) AS ?count)
                     WHERE {
                        ?subject a dbo:Actor .
                        ?subject a dbr:Film_Director
                     }
                     """) 
    return list(res)
