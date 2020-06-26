import sqlalchemy

metadata = sqlalchemy.MetaData()

Archive = sqlalchemy.Table(
    'archive',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),  # noqa:A003
    sqlalchemy.Column('content', sqlalchemy.LargeBinary, nullable=False),
)
