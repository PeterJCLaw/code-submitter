import sqlalchemy

metadata = sqlalchemy.MetaData()

# As a team member you upload your archives prior to their being used to
# simulate matches.
Archive = sqlalchemy.Table(
    'archive',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
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

# As a team member you choose which of your uploaded archives is the one which
# should be used for simulating matches.
ChoiceHistory = sqlalchemy.Table(
    'choice_history',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('archive_id', sqlalchemy.ForeignKey('archive.id'), nullable=False),

    sqlalchemy.Column('username', sqlalchemy.String, nullable=False),

    sqlalchemy.Column(
        'created',
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
)
