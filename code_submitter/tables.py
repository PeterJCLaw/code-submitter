import enum

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
    sqlalchemy.Column('description', sqlalchemy.String, nullable=False),

    sqlalchemy.Column('username', sqlalchemy.String, nullable=False),

    sqlalchemy.Column(
        'created',
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
)

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


# After matches have been simulated, there are a number of artefacts which
# should be shared with the teams.

class ArtefactType(enum.Enum):
    Logs = 'logs'
    Animations = 'animations'


Artefact = sqlalchemy.Table(
    'artefact',
    metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column('content', sqlalchemy.LargeBinary, nullable=False),
    sqlalchemy.Column('type', sqlalchemy.Enum(ArtefactType), nullable=False),

    # Compound foreign key to the ChoiceForSession. This provides a link to the
    # team this artefact is availalbe to. When `choice_id` is null, this
    # indicates that the artefact is available to all teams.
    sqlalchemy.Column(
        'choice_id',
        sqlalchemy.ForeignKey('choice.id'),
        nullable=True,
    ),
    sqlalchemy.Column(
        'session_id',
        sqlalchemy.ForeignKey('session.id'),
        nullable=False,
    ),
    sqlalchemy.ForeignKeyConstraint(
        ('choice_id', 'session_id'),
        ('choice_for_session.choice_id', 'choice_for_session.session_id'),
        # This foreign key constraint only applies when both fields are populated
        match='SIMPLE',
    ),

    sqlalchemy.Column(
        'created',
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
)

# Constrain session_id such that we only allow one globally-visible artefact
# per session. This is to prevent accidentally uploading everything as
# visible to everyone.
sqlalchemy.Index(
    'unique_globally_visible_artefact_per_session',
    unique=True,
    sqlite_where=Artefact.c.choice_id.is_(None),
)
