#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

api = Api(app)

# -------------------- SESSION MANAGEMENT -------------------- #
class ClearSession(Resource):
    def delete(self):
        session['page_views'] = None
        session.pop('user_id', None)
        return {}, 204

# -------------------- ARTICLES -------------------- #
class IndexArticle(Resource):
    def get(self):
        articles = [article.to_dict() for article in Article.query.all()]
        return make_response(jsonify(articles), 200)

class ShowArticle(Resource):
    def get(self, id):
        article = Article.query.get(id)
        if not article:
            return {'error': 'Article not found'}, 404

        # Non-logged-in users have pageview limits
        if not session.get('user_id'):
            session['page_views'] = session.get('page_views') or 0
            session['page_views'] += 1

            if session['page_views'] > 3:
                return {'message': 'Maximum pageview limit reached'}, 401

        return jsonify(article.to_dict()), 200

# -------------------- AUTHENTICATION -------------------- #
class Login(Resource):
    def post(self):
        username = request.get_json().get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id
            return jsonify(user.to_dict()), 200
        return {}, 401

class Logout(Resource):
    def delete(self):
        session.pop('user_id', None)
        return {}, 204

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {}, 401
        user = User.query.get(user_id)
        if not user:
            return {}, 401
        return jsonify(user.to_dict()), 200

# -------------------- MEMBERS-ONLY ARTICLES -------------------- #
class MemberOnlyIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'message': 'Unauthorized'}, 401

        articles = [article.to_dict() for article in Article.query.filter_by(is_member_only=True).all()]
        return jsonify(articles), 200

class MemberOnlyArticle(Resource):
    def get(self, id):
        user_id = session.get('user_id')
        if not user_id:
            return {'message': 'Unauthorized'}, 401

        article = Article.query.filter_by(id=id, is_member_only=True).first()
        if not article:
            return {'error': 'Article not found'}, 404

        return jsonify(article.to_dict()), 200

# -------------------- REGISTER RESOURCES -------------------- #
api.add_resource(ClearSession, '/clear', endpoint='clear')
api.add_resource(IndexArticle, '/articles', endpoint='article_list')
api.add_resource(ShowArticle, '/articles/<int:id>', endpoint='show_article')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(MemberOnlyIndex, '/members_only_articles', endpoint='member_index')
api.add_resource(MemberOnlyArticle, '/members_only_articles/<int:id>', endpoint='member_article')

# -------------------- RUN APP -------------------- #
if __name__ == '__main__':
    app.run(port=5555, debug=True)
