# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import logging
import sys
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_talent_desc = db.Column(db.String(120))
    genres = db.relationship('Genre', backref='venue', lazy=True)
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name} {self.city}' \
               f' {self.state} {self.address} {self.phone} ' \
               f'{self.image_link} {self.facebook_link}>'

    def get_venue_id_dict(self):
        return {'id': self.id, 'name': self.name}


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(20), nullable=False)
    venue_id = db.Column(db.Integer,
                         db.ForeignKey('venues.id'), nullable=False)

    def __repr__(self):
        return f'<Genre {self.id} {self.genre} {self.venue_id}>'


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_venue_desc = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name} {self.city}' \
               f' {self.state} {self.phone} {self.genres} ' \
               f'{self.image_link} {self.facebook_link}>'

    def get_artist_id_name_dict(self):
        return {'id': self.id, 'name': self.name}


class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime,
                           nullable=False)
    venue_id = db.Column(db.Integer,
                         db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column(db.Integer,
                          db.ForeignKey('artists.id'), nullable=False)

    def __repr__(self):
        return f"<show_id: {self.id} venue_id: {self.venue_id} " \
               f"artist_id: {self.artist_id} start_time: {self.start_time}>"


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues/')
def venues():
    areas = Venue.query.distinct('city', 'state').all()
    venues_data = []
    for area in areas:
        venues = Venue.query.filter(Venue.city == area.city,
                                    Venue.state == area.state).all()
        venue_data = {
            'city': area.city,
            'state': area.state,
            'venues': [v.get_venue_id_dict() for v in venues]
        }
        venues_data.append(venue_data)
    return render_template('pages/venues.html', areas=venues_data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_string = request.form.get('search_term')
    result = Venue.query.filter(Venue.name.like(f'%{search_string}%')).all()
    response = {
        'count': len(result),
        'data': [venue.get_venue_id_dict() for venue in result]
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).first()
    genres = venue.genres
    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': [genre.genre for genre in genres],
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'facebook_link': venue.facebook_link,
        'image_link': venue.image_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_talent_desc,
        'past_shows_count': 0,
        'upcoming_shows_count': 0,
        'past_shows': [],
        'upcoming_shows': []
    }
    shows = venue.shows
    for show in shows:
        artist = Artist.query.filter(Artist.id == show.artist_id).first()
        show_details = {
            'artist_id': artist.id,
            'artist_name': artist.name,
            'artist_image_link': artist.image_link,
            'start_time': show.start_time
        }
        if show.start_time < datetime.now():
            data['past_shows_count'] += 1
            data['past_shows'].append(show_details)
        elif show.start_time > datetime.now():
            data['upcoming_shows_count'] += 1
            data['upcoming_shows'].append(show_details)
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    try:
        gen_list = []
        genres = request.form.getlist("genres")
        for g in genres:
            gen_list.append(Genre(genre=g))
        form_data = request.form.to_dict()
        venue = Venue(name=form_data['name'],
                      city=form_data['city'],
                      address=form_data['address'],
                      state=form_data['state'],
                      phone=form_data['phone'],
                      facebook_link=form_data['facebook_link'],
                      image_link=form_data['image_link'],
                      seeking_talent_desc=form_data['seeking_description']
                      )
        if form_data['seeking_talent']:
            venue.seeking_talent = True
        venue.genres = gen_list
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()

    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
        flash("Erron in adding venue: " +
              form_data['name'] + "Could not be listed")
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    venue = Venue.query.filter(Venue.id == venue_id).first()
    try:
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        flash(f'Venue with venue id: {venue_id} was successfully Deleted!')
    else:
        flash(f'Venue with venue id: {venue_id} can not be deleted')

    return render_template('pages/venues.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = [artist.get_artist_id_name_dict() for artist in artists]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term')
    result = Artist.query.filter(Artist.name.like(f'%{search_term}%')).all()
    response = {
        'count': len(result),
        'data': [artist.get_artist_id_name_dict() for artist in result]
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).first()
    genres = artist.genres[1:-1].split(',')
    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_venue_desc,
        'image_link': artist.image_link,
        'past_shows': [],
        'upcoming_shows': [],
        'past_shows_count': 0,
        'upcoming_shows_count': 0
    }

    for show in artist.shows:
        venue = Venue.query.filter(Venue.id == show.venue_id).first()
        venue_details = {
            'venue_id': venue.id,
            'venue_name': venue.name,
            'venue_image_link': venue.image_link,
            'start_time': show.start_time
        }
        if show.start_time < datetime.now():
            data['past_shows_count'] += 1
            data['past_shows'].append(venue_details)
        elif show.start_time > datetime.now():
            data['upcoming_shows_count'] += 1
            data['upcoming_shows'].append(venue_details)
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter(Artist.id == artist_id).first()
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.filter(Artist.id == artist_id).first()
    genres = request.form.getlist("genres")
    error = False
    try:
        artist.name = request.form.get('name')
        artist.city = request.form.get('city')
        artist.state = request.form.get('state')
        artist.phone = request.form.get('phone')
        artist.genres = genres
        artist.facebook_link = request.form.get('facebook_link')
        artist.image_link = request.form.get('image_link')
        if request.form.get('seeking_venue'):
            artist.seeking_venue = True
        if request.form.get('seeking_description'):
            artist.seeking_venue_desc = request.form.get('seeking_description')
        print(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        app.logger.debug(request.form)
        print(sys.exc_info())
    finally:
        db.session.close()

    if not error:
        flash('Artist ' + request.form['name'] +
              ' was successfully Updated')
    else:
        flash('An error occurred. Artist ' +
              request.form['name'] + ' can not be Updated.')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue_obj = Venue.query.filter(Venue.id == venue_id).first()
    form = VenueForm(obj=venue_obj)
    # venue = {
    #     'id': venue_obj.id,
    #     'name': venue_obj.name,
    #     'genres': [g.genre for g in venue_obj.genres],
    #     'address': venue_obj.address,
    #     'city': venue_obj.city,
    #     'state': venue_obj.state,
    #     'phone': venue_obj.phone,
    #     'facebook_link': venue_obj.facebook_link,
    #     'seeking_talent': venue_obj.seeking_talent,
    #     'seeking_description': venue_obj.seeking_talent_desc,
    #     'image_link': venue_obj.image_link
    # }
    return render_template('forms/edit_venue.html', form=form, venue=venue_obj)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.filter(Venue.id == venue_id).first()
    genres = request.form.getlist("genres")
    gen_list = []
    for g in genres:
        gen_list.append(Genre(genre=g))
    error = False
    try:
        venue.name = request.form.get('name')
        venue.city = request.form.get('city')
        venue.state = request.form.get('state')
        venue.address = request.form.get('address')
        venue.phone = request.form.get('phone')
        venue.genres = gen_list
        venue.facebook_link = request.form.get('facebook_link')
        venue.image_link = request.form.get('image_link')
        if request.form.get('seeking_talent'):
            venue.seeking_talent = True
        venue.seeking_talent_desc = request.form.get('seeking_description')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if not error:
        flash('Venue ' + request.form['name'] +
              ' was successfully Updated')
    else:
        flash('An error occurred. Venue ' +
              request.form['name'] + ' can not be Updated.')
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    genres = request.form.getlist('genres')
    data = request.form.to_dict()
    error = False
    print(data)
    print(genres)
    try:
        artist = Artist(name=data['name'],
                        city=data['city'],
                        state=data['state'],
                        phone=data['phone'],
                        genres=genres,
                        facebook_link=data['facebook_link'],
                        image_link=data['image_link'],
                        seeking_venue_desc=data['seeking_description']
                        )
        if data['seeking_venue']:
            artist.seeking_venue = True
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()
    if not error:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
        flash(f"An Error Occurred While adding the Artist, "
              f"Artist {data['name']} Could not be added.")
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    shows = Show.query.all()
    for show in shows:
        artist = Artist.query.filter(Artist.id == show.artist_id).first()
        venue = Venue.query.filter(Venue.id == show.venue_id).first()
        show_details = {
            'venue_id': venue.id,
            'venue_name': venue.name,
            'artist_name': artist.name,
            'artist_id': artist.id,
            'artist_image_link': artist.image_link,
            'start_time': show.start_time
        }
        data.append(show_details)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        data = request.form.to_dict()
        show = Show(artist_id=data['artist_id'],
                    venue_id=data['venue_id'],
                    start_time=data['start_time'])
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()
    if not error:
        flash('Show was successfully listed!')
    else:
        flash('An Error occured, show can not be created')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: '
                  '%(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
