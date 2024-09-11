
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from models import db, Influencer, Sponsor, Campaign, AdRequest, campaign_influencer_association
from functools import wraps
from datetime import datetime

@app.route('/influencer_login')
def influencer_login():
    return render_template('influencer_login.html')

@app.route('/influencer_login', methods=['POST'])
def influencer_login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('influencer_login'))

    influencer = Influencer.query.filter_by(username=username).first()

    if not influencer:
        flash('Username does not exist')
        return redirect(url_for('influencer_login'))

    if not check_password_hash(influencer.passhash, password):
        flash('Incorrect Password')
        return redirect(url_for('influencer_login'))

    session['influencer_id'] = influencer.id
    flash('Login successful!!')
    return redirect(url_for('influencer_home'))



@app.route('/influencer_register')
def influencer_register():
    return render_template('influencer_register.html')

@app.route('/influencer_register', methods=['POST'])
def influencer_register_post():
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    email = request.form.get('email')
    phone = request.form.get('phone')
    category = request.form.get('category')
    niche = request.form.get('niche')
    social_media_platform = request.form.get('social_media_platform')
    social_media_profile = request.form.get('social_media_profile')
    reach = request.form.get('reach')

    if not all([username, password, confirm_password, email, phone, category, niche, social_media_platform, social_media_profile, reach]):
        flash('All fields are required')
        return redirect(url_for('influencer_register'))

    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('influencer_register'))

    if Influencer.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('influencer_register'))

    if Influencer.query.filter_by(email=email).first():
        flash('Email already exists')
        return redirect(url_for('influencer_register'))

    passhash = generate_password_hash(password)

    new_influencer = Influencer(
        username=username,
        passhash=passhash,
        name=name,
        email=email,
        phone=phone,
        category=category,
        niche=niche,
        social_media_platform=social_media_platform,
        social_media_profile=social_media_profile,
        reach=reach
    )

    db.session.add(new_influencer)
    db.session.commit()

    return redirect(url_for('influencer_login'))

def influencer_auth_required(func):
    @wraps(func)
    def func2(*args, **kwargs):
        if 'influencer_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login first")
            return redirect(url_for('influencer_login'))
    return func2

@app.route('/influencer_profile')
@influencer_auth_required
def influencer_profile():
    influencer =  Influencer.query.get(session['influencer_id'])
    return render_template('influencer_profile.html', influencer=influencer)

@app.route('/influencer_profile', methods=['POST'])
@influencer_auth_required
def influencer_profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')
    category = request.form.get('category')
    niche = request.form.get('niche')
    social_media_platform = request.form.get('social_media_platform')
    social_media_profile = request.form.get('social_media_profile')
    reach = request.form.get('reach')

    influencer = Influencer.query.get(session['influencer_id'])

    if not username or not cpassword or not password:
        flash('Please fill out all required fields')
        return redirect(url_for('influencer_profile'))

    influencer = Influencer.query.get(session('influencer_id'))
    if not check_password_hash(influencer.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('influencer_profile'))

    if username != sponsor.username:
        new_username = Influencer.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect (url_for('influencer_profile'))

    new_password_hash = generate_password_hash(password)
    influencer.username = username
    influencer.passhash = new_password_hash
    influencer.name = name
    influencer.category = category
    influencer.niche = niche
    influencer.social_media_profile = social_media_profile
    influencer.social_media_platform = social_media_platform
    influencer.reach = reach

    db.session.commit()
    flash('Profile updated successfully')
    return redirect (url_for('influencer_profile'))


@app.route('/influencer_logout')
@influencer_auth_required
def influencer_logout():
    session.pop('influencer_id')
    return redirect(url_for('influencer_login'))


@app.route('/influencer/home')
@influencer_auth_required
def influencer_home():
    influencer_id = session.get('influencer_id')

    if influencer_id is None:
        flash("Please log in to view your home page.")
        return redirect(url_for('influencer_login'))
    
    influencer = Influencer.query.filter_by(id=influencer_id).first()
    
    if influencer is None:
        flash("Influencer not found. Please log in again.")
        return redirect(url_for('influencer_login'))

    campaigns = Campaign.query.filter((Campaign.visibility == 'public') & (Campaign.flagged == False)).all()
    other_influencers = Influencer.query.filter(Influencer.id != influencer_id).all()
    categories = ["Fashion", "Travel", "Gaming", "Food", "Fitness", "DIY&Crafts", "Music", "Finance&Investment", "Science&Engineering", "Sports"]

    return render_template('influencer_home.html', campaigns=campaigns, other_influencers=other_influencers, categories=categories, influencer=influencer)


@app.route('/campaign/interest/<int:campaign_id>', methods=['POST'])
@influencer_auth_required
def mark_interest(campaign_id):
    influencer_id = session.get('influencer_id')
    if influencer_id is None:
        flash("Please log in to show interest.")
        return redirect(url_for('influencer_login'))

    association = db.session.query(campaign_influencer_association).filter_by(
        campaign_id=campaign_id, influencer_id=influencer_id
    ).first()

    if not association:
        print(f"No association found, creating new one for Campaign ID: {campaign_id} and Influencer ID: {influencer_id}")
        stmt = campaign_influencer_association.insert().values(
            campaign_id=campaign_id, influencer_id=influencer_id, influencer_interest='Interested'
        )
    else:
        print(f"Found association, updating interest for Campaign ID: {campaign_id} and Influencer ID: {influencer_id}")
        stmt = campaign_influencer_association.update().where(
            (campaign_influencer_association.c.campaign_id == campaign_id) &
            (campaign_influencer_association.c.influencer_id == influencer_id)
        ).values(influencer_interest='Interested')

    db.session.execute(stmt)
    db.session.commit()
    flash('Your interest has been noted.')

    return redirect(url_for('influencer_home'))


@app.route('/campaign/disinterest/<int:campaign_id>', methods=['POST'])
@influencer_auth_required
def mark_disinterest(campaign_id):
    influencer_id = session.get('influencer_id')
    if influencer_id is None:
        flash("Please log in to show disinterest.")
        return redirect(url_for('influencer_login'))

    association = db.session.query(campaign_influencer_association).filter_by(
        campaign_id=campaign_id, influencer_id=influencer_id
    ).first()

    if not association:
        print(f"No association found, creating new one for Campaign ID: {campaign_id} and Influencer ID: {influencer_id}")
        stmt = campaign_influencer_association.insert().values(
            campaign_id=campaign_id, influencer_id=influencer_id, influencer_interest='Not Interested'
        )
    else:
        print(f"Found association, updating interest for Campaign ID: {campaign_id} and Influencer ID: {influencer_id}")
        stmt = campaign_influencer_association.update().where(
            (campaign_influencer_association.c.campaign_id == campaign_id) &
            (campaign_influencer_association.c.influencer_id == influencer_id)
        ).values(influencer_interest='Not Interested')

    db.session.execute(stmt)
    db.session.commit()
    flash('Your disinterest has been noted.')

    return redirect(url_for('influencer_home'))



@app.route('/influencer/adrequests', methods=['GET'])
@influencer_auth_required
def influencer_adrequests():
    influencer_id = session.get('influencer_id')
    if influencer_id is None:
        flash("Please log in to view your ad requests.")
        return redirect(url_for('influencer_login'))
    
    ad_requests = AdRequest.query.filter_by(influencer_id=influencer_id, status='Pending').all()    
    return render_template('influencer_adrequests.html', ad_requests=ad_requests)

    
@app.route('/influencer/accept_offer/<int:ad_request_id>', methods=['POST'])
@influencer_auth_required
def influencer_accept_offer(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    ad_request.status = 'Accepted'
    
    db.session.commit()
    
    flash('Offer accepted.', 'success')
    return redirect(url_for('influencer_adrequests'))

@app.route('/influencer/reject_offer/<int:ad_request_id>', methods=['POST'])
@influencer_auth_required
def influencer_reject_offer(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    ad_request.status = 'Rejected'
    
    db.session.commit()
    
    flash('Offer rejected.', 'danger')
    return redirect(url_for('influencer_adrequests'))


@app.route('/influencer/campaigns')
@influencer_auth_required
def influencer_campaigns():
    influencer_id = session.get('influencer_id')
    campaigns_with_ad_requests = db.session.query(Campaign, AdRequest).join(AdRequest, Campaign.id == AdRequest.campaign_id).filter(
        AdRequest.influencer_id == influencer_id,
        AdRequest.status == 'Accepted'
    ).all()
    
    return render_template('influencer_campaigns.html', campaigns_with_ad_requests=campaigns_with_ad_requests)


