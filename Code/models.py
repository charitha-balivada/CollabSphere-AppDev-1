from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()
db.init_app(app=app)

# Association table for many-to-many relationship between Campaign and Influencer
campaign_influencer_association = db.Table('campaign_influencer_association',
    db.Column('campaign_id', db.Integer, db.ForeignKey('campaign.id'), primary_key=True),
    db.Column('influencer_id', db.Integer, db.ForeignKey('influencer.id'), primary_key=True),
    db.Column('influencer_interest', db.String(50), nullable=False, default='Not Interested')
)


class Influencer(db.Model):
    __tablename__ = 'influencer'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    niche = db.Column(db.String(256), nullable=False)
    reach = db.Column(db.Integer, nullable=False)
    social_media_profile = db.Column(db.String(256), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    social_media_platform = db.Column(db.String(32), nullable=False)
    flagged = db.Column(db.Boolean, default=False)

    
    campaigns = db.relationship('Campaign', secondary=campaign_influencer_association, back_populates='influencers')


class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    company_or_individual = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    industry = db.Column(db.String(32), nullable=False)
    niche = db.Column(db.String(256), nullable=False)
    business_link = db.Column(db.String(256), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    flagged = db.Column(db.Boolean, default=False)

    
    campaigns = db.relationship('Campaign', back_populates='sponsor')

class AdRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    messages = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    payment_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')
    

    campaign = db.relationship('Campaign', backref='ad_requests')
    influencer = db.relationship('Influencer', backref='ad_requests')


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(10), nullable=False)
    goals = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(32), nullable=False)
    flagged = db.Column(db.Boolean, default=False)

    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    sponsor = db.relationship('Sponsor', back_populates='campaigns')

    
    influencers = db.relationship('Influencer', secondary=campaign_influencer_association, back_populates='campaigns')

    
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False, default=1)
    admin = db.relationship('Admin', back_populates='campaigns')



class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(150), nullable=False)

    
    campaigns = db.relationship('Campaign', back_populates='admin')


with app.app_context():
    db.create_all()
    admin=Admin.query.filter_by(username='admin').first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin=Admin(username='admin',password_hash=password_hash,name="Admin")
        db.session.add(admin)
        db.session.commit()