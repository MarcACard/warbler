"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config["WTF_CSRF_ENABLED"] = False

# Disable Debug Toolbar for Debugging Unit Tests
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False
app.debug = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    ####################
    ## Setup & Teardown

    def setUp(self):
        """Create test client, add sample data."""

        # Reset Test DB Tables
        db.session.close()
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None,
        )

        db.session.commit()

    def test_add_message(self):
        """Add Message Route Test
        GIVEN a logged in user
        WHEN a message is posted
        THEN user is redirected (302) to the homepage.
        """

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
            self.assertIn(f"/users/{self.testuser.id}", resp.location)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    
    def test_add_message_unauthorized(self):
        """Add Message Route Test
        GIVEN a user that isn't logged in
        WHEN a message is posted
        THEN a message should NOT be added. 
        """

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"})

            # No message should be present. 
            msg = Message.query.first()
            self.assertIsNone(msg)

    def test_delete_message(self):
        """Add Message Route Test
        GIVEN a logged in user
        WHEN a message is deleted
        THEN message is deleted and user is redircted to the homepage
        """

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Post new message
            c.post("/messages/new", data={"text": "Hello"})
            m = Message.query.first()
            
            # Delete Posted Message
            resp = c.post(f"/messages/{m.id}/delete")
            m = Message.query.first() 
            
            # User is redirected & message does not exist. 
            self.assertEqual(resp.status_code, 302)
            self.assertIsNone(m)

    def test_delete_message_unauthorized(self):
        """Add Message Route Test
        GIVEN a user that isn't logged in
        WHEN attemtping to delete a message
        THEN user should be redirected & shown an 'unauthorized' message. 
        """

        with self.client as c:
            # Message does not exist, but user should be redirected before the DB is queried. 
            resp = c.post("/messages/1/delete", follow_redirects=True)

            self.assertIn(b"Access unauthorized.", resp.data)
            