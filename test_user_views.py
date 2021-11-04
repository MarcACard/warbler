"""User View Tests"""

import os
from unittest import TestCase
from models import db, connect_db, Message, User
from app import app, CURR_USER_KEY, do_logout

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Don't have WTForms use CSRF at all, since it's a pain to test
app.config["WTF_CSRF_ENABLED"] = False

# Disable Debug Toolbar for Debugging Unit Tests
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
app.debug = False


class UserViewTestCase(TestCase):
    """Test User Views."""

    ####################
    ## Setup & Teardown

    def setUp(self):
        # Reset Test DB Tables
        db.session.close()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        # Create Test User Account
        self.u = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None,
        )

        db.session.commit()

    ###########
    # HOMEPAGE

    def test_anon_homepage(self):
        """ Anon Homepage
        GIVEN no user logged in
        WHEN homepage accessed
        THEN direct to anon homepage
        """

        with self.client as c:
            resp = c.get("/")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                b"Sign up now to get your own personalized timeline!", resp.data
            )

    def test_user_homepage(self):
        """ User Homepage w/ Warble Message Feed
        GIVEN a logged in user
        WHEN navigating to the homepage
        THEN serve homepage with message feed
        """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u.id

            resp = c.get("/")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'id="messages"', resp.data)

    ##############
    # USER SIGNUP

    def test_user_signup(self):
        """Sign up Route - GET
        GIVEN a user that isn't signed in
        WHEN navigating to the /signup route
        THEN signup form should be available to the user
        """

        with self.client as c:

            resp = c.get("/signup")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"Join Warbler today.", resp.data)
            self.assertIn(b'<form method="POST" id="user_form">', resp.data)

    def test_user_signup_redirect(self):
        """Sign up Route - GET - Redirect
        GIVEN a logged in user
        WHEN navigating to the signup route
        THEN the user should be redircted to their homepage
        """

        with self.client as c: 
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u.id
        
        resp = c.get("/signup")
        resp_follow = c.get("/signup", follow_redirects=True)

        self.assertEqual(resp.status_code, 302)
        self.assertIn(b'id="messages"', resp_follow.data)
        

    def test_user_signup_post_valid(self):
        """Sign up Route - POST
        GIVEN a 
        WHEN a valid signup post request is submitted
        THEN create new account and redirect to the homepage
        """

        with self.client as c:
            resp = c.post(
                "/signup",
                data={
                    "username": "testSignUp",
                    "password": "TeStPasSwOrD",
                    "email": "testSignup@test.com",
                    "image_url": "",
                },
            )

            # Confirm Response & Redirect to homepage
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.location, "http://localhost/")

            # Confirm that User was created in DB
            u = User.query.filter(User.username == "testSignUp").first()
            self.assertIsNotNone(u)
            self.assertEqual(u.username, "testSignUp")

    def test_user_signup_post_invalid(self):
        """Sign up Route - POST - INVALID
        WHEN an invalid signup post request is submitted
        THEN redirect sign page with flash warnings
        """
        with self.client as c:
            resp = c.post(
                "/signup",
                data={
                    "username": "testSignUp",
                    "password": "",
                    "email": "testSignup@test.com",
                    "image_url": "",
                },
                follow_redirects=True,
            )

            # Confirm Response & Form Presence
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'<form method="POST" id="user_form">', resp.data)
            self.assertIn(b"Field must be at least 6 characters long.", resp.data)

    ###############
    # USER PROFILE

    def test_user_profile_owner_view(self):
        """
        GIVEN a logged in user
        WHEN user visits their profile
        THEN edit and delete profile buttons are visible
        """

        with self.client as c: 
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u.id

            resp =  c.get(f"/users/{self.u.id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(b'Edit Profile', resp.data)
            self.assertIn(b"Delete Profile", resp.data)
