"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User
from sqlalchemy import exc

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test User Model"""

    ####################
    ## Setup & Teardown

    def setUp(self):
        """Create test client, add sample data."""

        # Reset Test DB Tables
        db.session.close()
        db.drop_all()
        db.create_all()

        u1 = User.signup(
            email="user1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD",
            image_url=None,
        )

        u2 = User.signup(
            email="user2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD",
            image_url=None,
        )

        db.session.commit()

        self.u1 = u1
        self.u2 = u2

        self.client = app.test_client()

    ######################
    ## User Instance Attr

    def test_new_user(self):
        """Test User Instance Attributes
        WHEN a user is instantiated with the User Class
        THEN a user instance is returned
        """

        u = User(
            email="testmodel@test.com", username="testmodel", password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # Check __repr__
        self.assertEqual(repr(u), f"<User #{u.id}: {u.username}, {u.email}>")

        # Check User Attributes
        self.assertEqual(u.username, "testmodel")
        self.assertEqual(u.email, "testmodel@test.com")
        self.assertEqual(u.image_url, "/static/images/default-pic.png")
        self.assertEqual(u.header_image_url, "/static/images/warbler-hero.jpg")

        # User should have no messages, no followers, & no likes
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.likes), 0)

    ############################################
    ## Followers, Following, and Related Methods

    def test_followers_following(self):
        """Test User Instance follower and following properties
        GIVEN a user instance
        WHEN user1 follows user2
        THEN user1.following should equal 1 and user2 followers equal 1
        """

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)

    def test_is_followed_by_true(self):
        """Test User.is_followed_by method - Is Following
        GIVEN a user is following another user
        WHEN is_followed_by method is called
        THEN the method will return true
        """
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertFalse(self.u1.is_followed_by(self.u2))
        self.assertTrue(self.u2.is_followed_by(self.u1))

    def test_is_following_false(self):
        """Test User.is_following method - Is NOT Following
        GIVEN a user not following another user
        WHEN the is_following method is called
        THEN the method will return false
        """

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_following_true(self):
        """Test User.is_following method - True
        GIVEN a user is following another user
        WHEN the is_following method is called
        THEN the method will return true
        """

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))

    def test_is_followed_by_false(self):
        """Test User.is_followed_by method
        GIVEN a user not following another user
        WHEN when is_followed_by method is called
        THEN the method will return false
        """

        self.assertFalse(self.u1.is_followed_by(self.u2))
        self.assertFalse(self.u2.is_followed_by(self.u1))

    ##########
    ## Signup

    def test_user_signup(self):
        """Valid User Signup Test
        GIVEN a User Object and valid signup information
        WHEN the signup method is called
        THEN a User instance is returned with a hashed password
        """

        u = User.signup(
            username="TestSignup",
            email="TestSignup@test.com",
            password="Test_Password$!",
            image_url="https://test.com/image.png",
        )

        self.assertIsNotNone(u)
        self.assertIsInstance(u, User)
        self.assertEqual(u.username, "TestSignup")
        self.assertEqual(u.email, "TestSignup@test.com")
        self.assertEqual(u.image_url, "https://test.com/image.png")
        self.assertIn("$2b$", u.password)

    def test_user_invalid_signup(self):
        """Invalid User Signup - Duplicate Username Test
        GIVEN a new user instance with a duplicate username
        WHEN the session is committed to the psql db
        THEN an IntegrityError should be raised
        """
        u1 = User.signup(
            email="user1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD",
            image_url="https://test.com/image.png",
        )

        self.assertRaises(exc.IntegrityError, db.session.commit)

    ##################
    ## Authentication

    def test_user_authentication(self):
        """Valid User Authentication Test
        GIVEN valid user credentials
        WHEN the authenticate method is called
        THEN the specified user instance should be returned
        """
        u = User.authenticate(
            username="testuser1",
            password="HASHED_PASSWORD",
        )

        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.u1.id)

    def test_user_invalid_auth(self):
        """Invalid User Authentication Test
        GIVEN invalid user credentials
        WHEN the authentication method is called
        THEN False will be returned
        """

        u = User.authenticate(
            username="testuser1",
            password="Not the right password",
        )

        self.assertFalse(u)
