from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Genre, Movie

engine = create_engine('sqlite:///movies.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

session.query(User).delete()
session.query(Genre).delete()
session.query(Movie).delete()
session.commit()


# Initial setup user
user1 = User(email="robot@python.com", picture=' ')
session.add(user1)
session.commit()


# Genre - Drama
genre1 = Genre(name="Drama", user=user1)
session.add(genre1)
session.commit()

movie1 = Movie(title="The Shawshank Redemption", description="Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                rating="R", year="1994", genre=genre1, user=user1)
session.add(movie1)
session.commit()

movie2 = Movie(title="The Godfather", description="The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                rating="R", year="1972", genre=genre1, user=user1)
session.add(movie2)
session.commit()

movie4 = Movie(title="Pulp Fiction", description="The lives of two mob hit men, a boxer, a gangster's wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
                rating="R", year="1994", genre=genre1, user=user1)
session.add(movie4)
session.commit()

movie5 = Movie(title="Fight Club", description="An insomniac office worker, looking for a way to change his life, crosses paths with a devil-may-care soap maker, forming an underground fight club that evolves into something much, much more.",
                rating="R", year="1999", genre=genre1, user=user1)
session.add(movie5)
session.commit()

movie6 = Movie(title="Forest Gump", description="JFK, LBJ, Vietnam, Watergate, and other history unfold through the perspective of an Alabama man with an IQ of 75.",
                rating="PG-13", year="1994", genre=genre1, user=user1)
session.add(movie6)
session.commit()


# Genre - Action
genre2 = Genre(name="Action", user=user1)
session.add(genre2)
session.commit()

movie3 = Movie(title="The Dark Knight", description="When the menace known as the Joker emerges from his mysterious past, he wreaks havoc and chaos on the people of Gotham, the Dark Knight must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                rating="PG-13", year="2008", genre=genre2, user=user1)
session.add(movie3)
session.commit()

movie7 = Movie(title="Star Wars: Episode V - The Empire Strikes Back", description="After the rebels are overpowered by the Empire on their newly established base, Luke Skywalker begins Jedi training with Master Yoda. His friends accept shelter from a questionable ally as Darth Vader hunts them in a plan to capture Luke.",
                rating="PG", year="1980", genre=genre2, user=user1)
session.add(movie7)
session.commit()

movie8 = Movie(title="Inception",description="A thief, who steals corporate secrets through use of dream-sharing technology, is given the inverse task of planting an idea into the mind of a CEO.",
                rating="PG-13", year="2010", genre=genre2, user=user1)
session.add(movie8)
session.commit()

movie9 = Movie(title="The Matrix", description="A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
                rating="R", year="1999", genre=genre2, user=user1)
session.add(movie9)
session.commit()

movie10 = Movie(title="Star Wars: Episode IV - A New Hope", description="Luke Skywalker joins forces with a Jedi Knight, a cocky pilot, a Wookiee, and two droids to save the galaxy from the Empire's world-destroying battle-station, while also attempting to rescue Princess Leia from the evil Darth Vader.",
                rating="PG", year="1977", genre=genre2, user=user1)

print "added movies!"
