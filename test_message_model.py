"""Message model tests."""

import os
from unittest import TestCase

from models import db, User, Message, Likes
from sqlalchemy import exc
from app import app

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


class MessageLikeModelTestCase(TestCase):
    """Test Message Model & Likes Model"""

    ####################
    ## Setup & Teardown

    def setUp(self):
        """Setup before running unit tests."""

        # Reset Test DB Tables
        db.session.close()
        db.drop_all()
        db.create_all()

        # Sample User
        u1 = User.signup(
            username="TestUser",
            email="test@test.com",
            password="bad_password",
            image_url=None,
        )

        db.session.commit()

        self.u1 = u1

    ########################
    ## Message Instance Attr

    def test_new_message(self):
        """New Message Instance Test
        WHEN a message is initialized
        THEN a message instance is created
        """

        m = Message(
            text="Warbler like you've never warbled before #WarblerLife",
            user_id=self.u1.id,
        )

        self.assertIsNotNone(m)
        self.assertIsInstance(m, Message)
        self.assertEqual(
            m.text, "Warbler like you've never warbled before #WarblerLife"
        )
        self.assertEqual(m.user_id, self.u1.id)

    #########################
    ## Message User Reference

    def test_user_message_ref(self):
        """User Message Relationship
        GIVEN a message instance
        WHEN message is committed to the DB
        THEN message is accessible through the user.messages relationship
        """

        m = Message(
            text="Warbler like you've never warbled before #WarblerLife",
            user_id=self.u1.id,
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.u1.messages), 1)

    #######################
    ## Message Likes Model

    def test_liked_message(self):
        """Like Model
        GIVEN a user and message instance
        WHEN a user likes a message
        THEN message with be added to user's liked messages
        """

        m = Message(
            text="Warbler like you've never warbled before #WarblerLife",
            user_id=self.u1.id,
        )

        db.session.add(m)
        db.session.commit()

        self.u1.likes.append(m)

        db.session.commit()

        self.assertEqual(len(self.u1.likes), 1)
        self.assertEqual(self.u1.likes[0].id, m.id)
