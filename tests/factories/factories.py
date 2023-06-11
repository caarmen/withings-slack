from factory import Faker, SelfAttribute, SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from slackhealthbot.database.models import FitbitUser, User, WithingsUser


class WithingsUserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = WithingsUser

    user_id = Faker("pyint")
    oauth_access_token = Faker("pystr")
    oauth_refresh_token = Faker("pystr")
    oauth_userid = Faker("pystr")
    oauth_expiration_date = Faker("date_time")
    last_weight = Faker("pyfloat")


class FitbitUserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = FitbitUser

    user_id = Faker("pyint")
    oauth_access_token = Faker("pystr")
    oauth_refresh_token = Faker("pystr")
    oauth_userid = Faker("pystr")
    oauth_expiration_date = Faker("date_time")


class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User

    id = Faker("pyint")
    slack_alias = Faker("pystr")
    withings = SubFactory(WithingsUserFactory, user_id=SelfAttribute("..id"))
    fitbit = SubFactory(FitbitUserFactory, user_id=SelfAttribute("..id"))
