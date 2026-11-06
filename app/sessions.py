import secrets
from datetime import datetime, timezone

from flask.sessions import SessionInterface, SessionMixin, TaggedJSONSerializer
from werkzeug.datastructures import CallbackDict

from .db import get_conn, query_one


class PostgresSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        self.modified = False

        def on_update(_session):
            self.modified = True

        super().__init__(initial, on_update)
        self.sid = sid
        self.new = new


class PostgresSessionInterface(SessionInterface):
    session_class = PostgresSession
    serializer = TaggedJSONSerializer()

    def open_session(self, app, request):
        sid = request.cookies.get(self.get_cookie_name(app))
        if sid:
            row = query_one(
                """
                SELECT session_data
                FROM sessions
                WHERE session_id = %s AND expires_at > now()
                """,
                (sid,),
            )
            if row is not None:
                data = self.serializer.loads(row["session_data"])
                return self.session_class(data, sid=sid)

        return self.session_class(sid=secrets.token_urlsafe(32), new=True)

    def save_session(self, app, session, response):
        cookie_name = self.get_cookie_name(app)
        cookie_domain = self.get_cookie_domain(app)
        cookie_path = self.get_cookie_path(app)

        if not session:
            if session.modified:
                get_conn().execute(
                    "DELETE FROM sessions WHERE session_id = %s",
                    (session.sid,),
                )
            response.delete_cookie(
                cookie_name,
                domain=cookie_domain,
                path=cookie_path,
                secure=self.get_cookie_secure(app),
                httponly=self.get_cookie_httponly(app),
                samesite=self.get_cookie_samesite(app),
            )
            return

        if session.modified or session.new or self.should_set_cookie(app, session):
            expires_at = datetime.now(timezone.utc) + app.permanent_session_lifetime
            session_data = self.serializer.dumps(dict(session))
            get_conn().execute(
                """
                INSERT INTO sessions (session_id, session_data, expires_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE
                SET session_data = EXCLUDED.session_data,
                    expires_at = EXCLUDED.expires_at
                """,
                (session.sid, session_data, expires_at),
            )

        expires = self.get_expiration_time(app, session)
        response.set_cookie(
            cookie_name,
            session.sid,
            expires=expires,
            httponly=self.get_cookie_httponly(app),
            secure=self.get_cookie_secure(app),
            samesite=self.get_cookie_samesite(app),
            domain=cookie_domain,
            path=cookie_path,
        )

    def regenerate(self, session):
        get_conn().execute(
            "DELETE FROM sessions WHERE session_id = %s",
            (session.sid,),
        )
        session.sid = secrets.token_urlsafe(32)
        session.new = True
        session.modified = True
