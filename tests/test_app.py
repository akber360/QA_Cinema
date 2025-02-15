import pytest
from flask import url_for, session
from flask_testing import TestCase
from application import app, db
from models import User, Screen, Movie, Screening, Discussion, Booking, BookingDetail
import os
from werkzeug.security import generate_password_hash


class TestBase(TestCase):
    def create_app(self):
        app.config.update(
            SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI"),
            DEBUG=True,
            WTF_CSRF_ENABLED=False
        )
        return app
    
    def setUp(self):

        self.client = app.test_client()

        db.drop_all()
        db.create_all()

        test_user = User(
            username="testuser",
            email="testuser@example.com",
            password= generate_password_hash("password123",method='pbkdf2:sha256', salt_length=8),
            address="123 Test St",
            first_name="Test",
            last_name="User",
            card_number="1234567890123456",
            card_expiry="12/24",
            card_cvc=123
        )
        db.session.add(test_user)
        db.session.commit()

        test_movies =  [
            Movie(title="Test_Movie(classic)", director="Test Director", actors="Actor1, Actor2, Actor3", release_date="2023-01-01", description="A test movie description", poster="movie_poster.jpg", classic=True, age_restricted=False),
            Movie(title="Test_Movie(new release)", director="Test Director", actors="Actor1, Actor2, Actor3", release_date="2023-01-01", description="A test movie description", poster="movie_poster2.jpg", classic=False, age_restricted=True),
            Movie(title="Film123", director="Test Director", actors="Actor1, Actor2, Actor3", release_date="2023-01-01", description="A test movie description", poster="movie_poster3.jpg", classic=True, age_restricted=True)
        ]
        db.session.add_all(test_movies)
        db.session.commit()

        test_screens = [
            Screen(standard=True),
            Screen(standard=False, seating_capacity=59)
        ]
        db.session.add_all(test_screens)
        db.session.commit()

        test_screenings = [
            Screening(movie_id=1, screen_id=1, time="12:00:00", day ="Friday", current_capacity=100),
            Screening(movie_id=2, screen_id=2, time="13:00:00", day ="Saturday", current_capacity=25)
        ]  
        db.session.add_all(test_screenings)
        db.session.commit()

        test_discussions = [
            Discussion(username=test_user.username, movie_id=1, topic="Test Topic 1", responding_to="Post", content="Test content for Test Topic 1", timestamp="01/01/2023 12:00"),
            Discussion(username=test_user.username, movie_id=2, topic="Test Topic 2", responding_to="Post", content="Test content for Test Topic 2", timestamp="01/01/2023 12:30"),
            Discussion(username=test_user.username, movie_id=1, topic="Test Topic 1", responding_to=1, content="Test comment for Test Topic 1", timestamp="01/01/2023 13:00"),
        ]
        db.session.add_all(test_discussions)
        db.session.commit()

    def tearDown(self):
        session.clear()
        db.session.remove()
        db.drop_all()


class TestStaticPages(TestBase):
    def test_home_get(self):
        response = self.client.get(url_for("home"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Bringing Stories to Life, One Screen at a Time", response.data)
    
    def test_about_get(self):
        response = self.client.get(url_for("about"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Who We Are", response.data)

    def test_opening_times_get(self):
        response = self.client.get(url_for("opening_times"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"QA Cinema Opening Times", response.data)
    
    def test_classifications_get(self):
        response = self.client.get(url_for("classifications"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Film Classifications", response.data)

    def test_screens_get(self):
        response = self.client.get(url_for("screens"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"standard cinema screen", response.data)

    def test_cinema_services_get(self):
        response = self.client.get(url_for("cinema_services"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"QA Cinema Services", response.data)

    def test_view_movie_get(self):
        response = self.client.get(url_for("view_movie", movie_id=1))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test_Movie(classic)", response.data)

    def test_listings_get(self):
        response = self.client.get(url_for("listings"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test_Movie(classic)", response.data)
        self.assertIn(b"Test_Movie(new release)", response.data)

    def test_new_releases_get(self):
        response = self.client.get(url_for("new_releases"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test_Movie(new release)", response.data)
        self.assertNotIn(b"Test_Movie(classic)", response.data)

    def test_classics_get(self):
        response = self.client.get(url_for("classics"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test_Movie(classic)", response.data)
        self.assertNotIn(b"Test_Movie(new release)", response.data)

    def test_search_results_post(self):
        response = self.client.post(
            url_for("search_results"),
            data = {
                "searchinput":"Test"
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test_Movie(classic)", response.data)
        self.assertIn(b"Test_Movie(new release)", response.data)
        self.assertNotIn(b"Film123", response.data)


class TestAPI(TestBase):
    def test_api_view_screenings_get(self):
        response = self.client.get(
            url_for("api_view_screenings", movie_id=1),
            query_string={"day": "Friday"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"12:00:00", response.data)

    def test_api_view_screenings_no_screenings(self):
        response = self.client.get(
            url_for("api_view_screenings", movie_id=3),
            query_string={"day": "Friday"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"There are currently no showings of this film", response.data)


class TestPayment(TestBase):
    def test_payment_get(self):
        response = self.client.get(url_for("payment", screening_id=1))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test_Movie(classic)", response.data)
        self.assertIn(b"Friday", response.data)
        self.assertIn(b"12:00:00", response.data)
    
    def test_payment_post(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"

        response = self.client.post(
            url_for("payment", screening_id=1),
            data = {
                "first_name":"Payment",
                "last_name":"Test",
                "address":"Payment Test",
                "card_number":"9876543219876543",
                "card_expiry":"10/25",
                "card_cvc": 456
            }
        )
        self.assertEqual(response.status_code, 200)
        test_payment = User.query.filter_by(username="testuser").first()
        self.assertIsNotNone(test_payment)
        self.assertEqual(test_payment.first_name, "Payment")
        self.assertEqual(test_payment.last_name, "Test")
        self.assertEqual(test_payment.card_number, "9876543219876543")


class TestSignup(TestBase):
    def test_signup_get(self):
        response = self.client.get(url_for("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Already have an account?", response.data)

    def test_signup_post(self):
        response = self.client.post(
            url_for("signup"),
            data = {
                "username":"testuser2",
                "email":"testuser2@example.com",
                "password":"Password123$",
                "confirmation":"Password123$"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Don't have an account?", response.data)
        test_signup = User.query.filter_by(username="testuser2").first()
        self.assertIsNotNone(test_signup)
        self.assertEqual(test_signup.email, "testuser2@example.com")
    
    def test_unique_username(self):
        response = self.client.post(
            url_for("signup"),
            data = {
                "username":"testuser",
                "email":"testuser@example.com",
                "password":"Password123$",
                "confirmation":"Password123$"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Already have an account?", response.data)
    
    def test_password_mismatch(self):
        response = self.client.post(
            url_for("signup"),
            data = {
                "username":"testuser3",
                "email":"testuser3@example.com",
                "password":"Password123$",
                "confirmation":"Password123@"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Already have an account?", response.data)

    def test_password_security(self):
        response = self.client.post(
            url_for("signup"),
            data = {
                "username":"testuser3",
                "email":"testuser3@example.com",
                "password":"Password123",
                "confirmation":"Password123"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Already have an account?", response.data)


class TestLogin(TestBase):          
    def test_login_get(self):
        response = self.client.get(url_for("login"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Don't have an account?", response.data)

    def test_login_post(self):
        response = self.client.post(
            url_for("login"),
            data = {
                "username":"testuser",
                "password":"password123"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            self.assertEqual(session['username'], "testuser")
        self.assertIn(b"Bringing Stories to Life, One Screen at a Time", response.data)

    def test_login_no_account(self):
        response = self.client.post(
            url_for("login"),
            data = {
                "username":"testuser2",
                "password":"password123"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Already have an account?", response.data)
        self.assertIn(b"no account associated with this username - please sign up", response.data)

    def test_incorrect_user_password(self):
        response = self.client.post(
            url_for("login"),
            data = {
                "username":"testuser",
                "password":"wrongpassword"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Don't have an account?", response.data)


class TestLogout(TestBase):
    def test_logout_get(self):
        response = self.client.get(url_for("logout"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"successfully logged out.", response.data)
    
    def test_logout_post(self):
        response = self.client.post(
            url_for("logout"),
            follow_redirects = True
            )
        with self.client.session_transaction() as session:
            self.assertNotIn('username', session)
        self.assertIn(b"Bringing Stories to Life, One Screen at a Time", response.data)


class TestForum(TestBase):
    def test_forum_get(self):
        response = self.client.get(url_for("forum"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test Topic 1", response.data)
        self.assertIn(b"Test_Movie(classic)", response.data)
        self.assertIn(b"testuser", response.data)

    def test_post_to_forum(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.post(
            url_for("forum"),
            data = {
                "responding_to": "Post",
                "movie_id": 1,
                "topic": "Test Topic 3", 
                "content": "Test content for Test Topic 3"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Comment posted successfully!", response.data)
        self.assertIn(b"Test Topic 3", response.data)
    
    def test_comment_to_post(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.post(
            url_for("forum"),
            data = {
                "responding_to": 2,
                "movie_id": 2,
                "topic": "Test Topic 2", 
                "content": "Test comment for Test Topic 2" 
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Comment posted successfully!", response.data)
        self.assertIn(b"Test comment for Test Topic 2", response.data)
    
    def test_swearwords(self):
        with self.client.session_transaction() as session:
            session["username"] = "testuser"
        response = self.client.post(
            url_for("forum"),
            data = {
                "responding_to": "Post",
                "movie_id": 1,
                "topic": "Crap", 
                "content": "shit"
            },
            follow_redirects = True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Your topic contains inappropriate language!", response.data)
        self.assertIn(b"Your comment contains inappropriate language!", response.data)
        self.assertNotIn(b"Crap", response.data)
        self.assertNotIn(b"shit", response.data)


class TestBooking(TestBase):
    def test_booking_get(self):
        response = self.client.get(url_for("book_movie", screening_id=1))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Test_Movie(classic)", response.data)
        self.assertIn(b"12:00:00", response.data)
        self.assertIn(b"Friday", response.data)

    def test_booking_post(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
        response = self.client.post(
            url_for("book_movie", screening_id=1),
        data={
            "Adult":1,
            "Child":1,
            "Concession":1
            },
        follow_redirects = True
        )
        # check Booking database
        check_booking = Booking.query.filter_by(user_id=1).first()
        self.assertIsNotNone(check_booking)
        self.assertEqual(check_booking.total_price, 32.5)
        # check BookingDetail database
        check_booking_detail = BookingDetail.query.filter_by(booking_id=1).all()
        self.assertIsNotNone(check_booking_detail)
        self.assertEqual(check_booking_detail[0].ticket_type, "Adult")
        self.assertEqual(check_booking_detail[1].ticket_type, "Child")
        self.assertEqual(check_booking_detail[2].ticket_type, "Concession")
        # check redirect to Payment
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Payment Form", response.data)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")