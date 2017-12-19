# Build an Item Catalog Application
This project is part of Udacity's Full Stack Web Developer Nanodegree Program.
The objective was to build a web application using **flask** that provides a list of items within a variety of categories. The application also implements authorization and authentication using a Google Account. After signing in, a user has the ability to add, update, or delete items and categories. The application also provides JSON endpoints.

## Getting started
1. Install [Vagrant](https://www.vagrantup.com/).
2. Install [VirtualBox](https://www.virtualbox.org/).
3. Clone this repository
4. Launch the Vagrant VM (by typing ```vagrant up``` in the directory ```fullstack/vagrant``` from the terminal.)
5. Connect to the Vagrant VM session (by typing ```vagrant ssh``` from the terminal.)
6. Build movie database by typing ```python /vagrant/catalog/database_setup.py``` from the terminal.
7. Seed movie data by typing ```python /vagrant/catalog/lotsofmovies.py``` from the terminal.
8. Run the application within the VM by typing ```python /vagrant/catalog/application.py``` from the terminal.
9. Access the application by visiting http://localhost:5000

## Using JSON endpoints
1. Run the application following the **Getting started** steps above
2. Request movies for a given genre ID: ```/genres/<int:genre_id>/movies/JSON```
3. Request a specific movie given genre ID and movie ID: ```/genres/<int:genre_id>/movies/<int:movie_id>/JSON```
4. Request all genres: ```/genres/JSON```
5. Request all movies: ```/movies/JSON```
6. Request all users: ```/users/JSON```

## License
The contents of this repository are covered under the [MIT License](https://opensource.org/licenses/MIT).
