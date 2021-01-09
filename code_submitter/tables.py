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


# At the point of downloading the archives in order to run matches, you create a
# Session. The act of doing that will also create the required ChoiceForSession
# rows to record which items will be contained in the download.
Session = sqlalchemy.Table(
    'session',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('name', sqlalchemy.String, unique=True, nullable=False),

    sqlalchemy.Column('username', sqlalchemy.String, nullable=False),

    sqlalchemy.Column(
        'created',
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
)

# TODO: constrain such that each team can only have one choice per session?
ChoiceForSession = sqlalchemy.Table(
    'choice_for_session',
    metadata,
    sqlalchemy.Column(
        'choice_id',
        sqlalchemy.ForeignKey('choice_history.id'),
        primary_key=True,
    ),
    sqlalchemy.Column(
        'session_id',
        sqlalchemy.ForeignKey('session.id'),
        primary_key=True,
    ),
)
