from flask import Flask, abort, request
from flask_restful import Api, Resource, reqparse, inputs, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
import datetime
import sys

app = Flask(__name__)
api = Api(app)

# ================ DATABASE =====================
db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'


class Event(db.Model):
    __events__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.VARCHAR, nullable=False)
    date = db.Column(db.Date, nullable=False)


db.create_all()
# ================ PARSER =========================
parser = reqparse.RequestParser()


def RequiredPost():
    try:
        parser.remove_argument('start_time')
        parser.remove_argument('end_time')
    finally:
        parser.add_argument(
            'date',
            type=inputs.date,
            help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
            required=True
        )
        parser.add_argument(
            'event',
            type=str,
            help="The event name is required!",
            required=True
        )


def RequiredGet():
    try:
        parser.remove_argument('date')
        parser.remove_argument('event')
    finally:
        parser.add_argument(
            'start_time',
            type=inputs.date
        )
        parser.add_argument(
            'end_time',
            type=inputs.date
        )


# ================ RESOURCES ======================
resource_fields = {
    'id': fields.Integer,
    'event': fields.String,
    'date': fields.DateTime(dt_format='iso8601')
}


class GetToday(Resource):
    @marshal_with(resource_fields)
    def get(self):
        return Event.query.filter(Event.date == datetime.date.today()).all()


class GetEvent(Resource):
    # @marshal_with(resource_fields)
    def get(self):
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        if start_time and end_time:
            lists = []
            events = Event.query.filter(Event.date >= start_time, Event.date <= end_time).all()
            if len(events) < 1:
                abort(404, {"message": "The event doesn't exist!"})
            for e in events:
                el = {"id": e.id, "event": e.event, "date": str(e.date)}
                lists.append(el)
            return lists
        lists = []
        for e in Event.query.all():
            el = {"id": e.id, "event": e.event, "date": str(e.date)}
            lists.append(el)
        return lists

    def post(self):
        RequiredPost()
        args = parser.parse_args()
        name = args['event']
        date = str(args['date'].date())
        event = Event(event=name, date=args['date'])
        db.session.add(event)
        db.session.commit()
        return {'message': 'The event has been added!',
                'event': name, 'date': date
                }


class EventByID(Resource):
    @marshal_with(resource_fields)
    def get(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        return event

    def delete(self, event_id):
        event = Event.query.filter(Event.id == event_id).first()
        if event is None:
            abort(404, "The event doesn't exist!")
        db.session.delete(event)
        db.session.commit()
        return {'message': 'The event has been deleted!'}


api.add_resource(GetEvent, '/event/')
api.add_resource(GetToday, '/event/today')
api.add_resource(EventByID, '/event/<int:event_id>')

# ================ RUN =========================
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run(port=8080)
