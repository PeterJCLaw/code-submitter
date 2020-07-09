import sqlalchemy

metadata = sqlalchemy.MetaData()

Archive = sqlalchemy.Table(
    'archive',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),  # noqa:A003
    sqlalchemy.Column('content', sqlalchemy.LargeBinary, nullable=False),

    sqlalchemy.Column('username', sqlalchemy.String, nullable=False),
    sqlalchemy.Column('team', sqlalchemy.String, nullable=False),

    sqlalchemy.Column(
        'created',
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
)
