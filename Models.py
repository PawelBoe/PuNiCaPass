import datetime

from peewee import CharField, DateTimeField, IntegerField, Model, SqliteDatabase

db = SqliteDatabase("./database.sqlite")


class BaseModel(Model):
    class Meta:
        database = db


class NumericalValues(BaseModel):
    class Meta:
        table_name = "numerical_values"

    label = CharField(unique=True)
    value = IntegerField(default=0)

    processed = DateTimeField(default=datetime.datetime.now)


class OrganizationKeys(BaseModel):
    class Meta:
        table_name = "organization_keys"

    organization_name = CharField(unique=True)
    public_key_b64 = CharField()
    private_key_b64 = CharField()

    processed = DateTimeField(default=datetime.datetime.now)


class RevokedPasses(BaseModel):
    class Meta:
        table_name = "revoked_passes"

    pass_id = IntegerField(unique=True)

    processed = DateTimeField(default=datetime.datetime.now)
