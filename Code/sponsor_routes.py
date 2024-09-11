import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from models import db, Influencer, Sponsor, Campaign, AdRequest, campaign_influencer_association
from functools import wraps
from datetime import datetime
from sqlalchemy.orm import aliased

@app.route('/sponsor_login')
def sponsor_login():
    return render_template('sponsor_login.html')

@app.route('/sponsor_login', methods=['POST'])
def sponsor_login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('sponsor_login'))

    sponsor = Sponsor.query.filter_by(username=username).first()

    if not sponsor:
        flash('Username does not exist')
        return redirect(url_for('sponsor_login'))

    if not check_password_hash(sponsor.passhash, password):
        flash('Incorrect Password')
        return redirect(url_for('sponsor_login'))

    session['sponsor_id'] = sponsor.id
    flash('Login successful!!')
    return redirect(url_for('sponsor_home'))



@app.route('/sponsor_register')
def sponsor_register():
    return render_template('sponsor_register.html')

@app.route('/sponsor_register', methods=['POST'])
def sponsor_register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    company_or_individual = request.form.get('company_or_individual')
    name = request.form.get('name')
    confirm_password = request.form.get('confirm_password')
    email = request.form.get('email')
    phone = request.form.get('phone')
    industry = request.form.get('industry')
    niche = request.form.get('niche')
    business_link = request.form.get('business_link')
    

    # Check if all fields are provided
    if not all([username, password, confirm_password, company_or_individual, name, email, phone, industry, niche, business_link]):
        flash('All fields are required')
        return redirect(url_for('sponsor_register'))

    # Check if passwords match
    if password != confirm_password:
        flash('Passwords do not match')
        return redirect(url_for('sponsor_register'))

    # Check if username or email already exists
    if Sponsor.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('sponsor_register'))

    if Sponsor.query.filter_by(email=email).first():
        flash('Email already exists')
        return redirect(url_for('sponsor_register'))

    # Hash the password
    passhash = generate_password_hash(password)

    # Create a new sponsor
    new_sponsor = Sponsor(
        username=username,
        passhash=passhash,
        company_or_individual=company_or_individual,
        name=name,
        email=email,
        phone=phone,
        industry=industry,
        niche=niche,
        business_link=business_link
    )

    # Add and commit to the database
    db.session.add(new_sponsor)
    db.session.commit()

    return redirect(url_for('sponsor_login'))

def sponsor_auth_required(func):
    @wraps(func)
    def func4(*args, **kwargs):
        if 'sponsor_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login first")
            return redirect(url_for('sponsor_login'))
    return func4



@app.route('/sponsor_profile')
@sponsor_auth_required
def sponsor_profile():
    sponsor = Sponsor.query.filter_by(id=session['sponsor_id']).first()
    return render_template('sponsor_profile.html', sponsor=sponsor)

@app.route('/sponsor_profile', methods=['POST'])
@sponsor_auth_required
def sponsor_profile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    name = request.form.get('name')
    company_or_individual = request.form.get('company_or_individual')
    industry = request.form.get('industry')
    niche = request.form.get('niche')
    business_link = request.form.get('business_link')
    
    sponsor = Sponsor.query.get(session['sponsor_id'])

    if not username or not cpassword or not password:
        flash('Please fill out all required fields')
        return redirect(url_for('sponsor_profile'))

    sponsor = Sponsor.query.get(session('sponsor_id'))
    if not check_password_hash(sponsor.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('sponsor_profile'))

    if username != sponsor.username:
        new_username = Sponsor.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect (url_for('sponsor_profile'))

    new_password_hash = generate_password_hash(password)
    sponsor.username = username
    sponsor.passhash = new_password_hash
    sponsor.name = name
    sponsor.company_or_individual = company_or_individual
    sponsor.industry = industry
    sponsor.niche = niche
    sponsor.business_link = business_link
    db.session.commit()
    flash('Profile updated successfully')
    return redirect (url_for('sponsor_profile'))


@app.route('/sponsor_logout')
@sponsor_auth_required
def sponsor_logout():
    session.pop('sponsor_id')
    return redirect(url_for('sponsor_login'))


@app.route('/campaigns')
@sponsor_auth_required
def campaigns():
    sponsor = Sponsor.query.get(session['sponsor_id'])
    campaign = Campaign.query.filter_by(sponsor_id=session['sponsor_id']).all()
    return render_template('campaigns.html', campaigns=campaign, sponsor=sponsor)

@app.route('/campaigns/add_campaign')
@sponsor_auth_required
def add_campaign():
    sponsors = Sponsor.query.all()
    sponsor = Sponsor.query.get(session['sponsor_id'])
    return render_template('add_campaign.html', sponsor=sponsor)

@app.route('/campaigns/add_campaign', methods=['POST'])
@sponsor_auth_required
def add_campaign_post():
    name = request.form.get('name')
    description = request.form.get('description')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    budget = request.form.get('budget')
    visibility = request.form.get('visibility')
    goals = request.form.get('goals')
    category = request.form.get('category')
    sponsor_id = request.form.get('sponsor')

    # Check if all fields are provided
    if not all([name, description, start_date_str, end_date_str, budget, visibility, goals, category, sponsor_id]):
        flash('All fields are required')
        return redirect(url_for('add_campaign'))

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format')
        return redirect(url_for('add_campaign'))

    # Create a new campaign
    new_campaign = Campaign(
        name=name,
        description=description,
        start_date=start_date,
        end_date=end_date,
        budget=float(budget),
        visibility=visibility,
        goals=goals,
        category=category,
        sponsor_id=sponsor_id
    )

    # Add and commit to the database
    db.session.add(new_campaign)
    db.session.commit()
    flash('Campaign added successfully')
    return redirect(url_for('campaigns'))

@app.route('/campaign/<int:campaign_id>/edit')
@sponsor_auth_required
def edit_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    sponsors = Sponsor.query.all()
    sponsor = Sponsor.query.get(session['sponsor_id'])

    if not campaign:
        flash('Campaign not found')
        return redirect(url_for('company_activity'))
    return render_template('edit_campaign.html', campaign=campaign, sponsor=sponsor)

@app.route('/campaign/<int:campaign_id>/edit', methods=['POST'])
@sponsor_auth_required
def edit_campaign_post(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    sponsors = Sponsor.query.all()
    sponsor = Sponsor.query.get(session['sponsor_id'])

    title = request.form.get('title')
    description = request.form.get('description')
    budget = request.form.get('budget')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    status = request.form.get('status')
    category = request.form.get('category')
    visibility = request.form.get('visibility')
    goals = request.form.get('goals')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        flash('Invalid date format')
        return redirect(url_for('edit_campaign', campaign_id=campaign.id, sponsor=sponsor))

    campaign.title = title
    campaign.description = description
    campaign.budget = float(budget)
    campaign.start_date = start_date
    campaign.end_date = end_date
    campaign.status = status
    campaign.category = category
    campaign.visibility = visibility
    campaign.goals = goals
     

    db.session.commit()

    return redirect(url_for('campaigns'))

@app.route('/campaigns/<int:campaign_id>/delete')
@sponsor_auth_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    return render_template('delete_campaign.html', campaign=campaign)

@app.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
@sponsor_auth_required
def delete_campaign_post(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign has been deleted successfully.')
    return redirect(url_for('campaigns'))

@app.route('/sponsor_home')
@sponsor_auth_required
def sponsor_home():
    categories = ["Fashion", "Travel", "Gaming", "Food", "Fitness", "DIY&Crafts", "Music", "Finance&Investment", "Science&Engineering", "Sports"]
    influencers = Influencer.query.all()  # Query all influencers
    campaigns = Campaign.query.filter_by(visibility='public').all()  # Query only public campaigns
    sponsor = Sponsor.query.filter_by(id=session['sponsor_id']).first()
    return render_template('sponsor_home.html', categories=categories, influencers=influencers, campaigns=campaigns, sponsor=sponsor)

@app.route('/sponsor/adrequests/<int:influencer_id>')
@sponsor_auth_required
def adrequests(influencer_id):

    influencer = Influencer.query.get_or_404(influencer_id)
    sponsor = Sponsor.query.filter_by(id=session['sponsor_id']).first()
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id, flagged=False).all()

    return render_template('adrequests.html', influencer=influencer, campaigns=campaigns)

@app.route('/sponsor/adrequests/submit/<int:influencer_id>', methods=['POST'])
@sponsor_auth_required
def adrequest_post(influencer_id):

    campaign_id = request.form.get('campaign_id')
    messages = request.form.get('messages')
    requirements = request.form.get('requirements')
    payment_amount = request.form.get('payment_amount')

    new_ad_request = AdRequest(
        campaign_id=campaign_id,
        influencer_id=influencer_id,
        messages=messages,
        requirements=requirements,
        payment_amount=payment_amount,
        status="Pending"
    )

    # Add the new Ad Request to the database
    db.session.add(new_ad_request)
    db.session.commit()

    flash('Ad Request sent successfully!', 'success')
    return redirect(url_for('sponsor_home'))

@app.route('/sponsor/adrequests')
@sponsor_auth_required
def sponsor_adrequests():
    sponsor_id = session.get('sponsor_id')
    if sponsor_id is None:
        flash("Please log in to view your ad requests.")
        return redirect(url_for('sponsor_login'))

    sponsor = Sponsor.query.filter_by(id=sponsor_id).first()
    if not sponsor:
        flash("Sponsor not found.")
        return redirect(url_for('sponsor_login'))

    # Ad requests related to the sponsor's campaigns
    ad_requests = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == sponsor_id).all()

    # Interested influencers for the sponsor's campaigns
    interested_influencers = db.session.query(
        Influencer, Campaign
    ).select_from(campaign_influencer_association).join(
        Influencer, campaign_influencer_association.c.influencer_id == Influencer.id
    ).join(
        Campaign, campaign_influencer_association.c.campaign_id == Campaign.id
    ).filter(
        Campaign.sponsor_id == sponsor_id,
        campaign_influencer_association.c.influencer_interest == 'Interested'
    ).all()

    return render_template('sponsor_adrequests.html', ad_requests=ad_requests, interested_influencers=interested_influencers)



@app.route('/sponsor/adrequest/edit/<int:ad_request_id>', methods=['GET', 'POST'])
@sponsor_auth_required
def sponsor_edit_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    if request.method == 'POST':
        ad_request.messages = request.form['messages']
        ad_request.requirements = request.form['requirements']
        ad_request.payment_amount = request.form['payment_amount']
        ad_request.status = request.form['status']
        db.session.commit()
        flash("Ad request updated successfully.")
        return redirect(url_for('sponsor_adrequests'))
    return render_template('sponsor_edit_ad_request.html', ad_request=ad_request)

@app.route('/sponsor/adrequest/delete/<int:ad_request_id>', methods=['POST'])
@sponsor_auth_required
def sponsor_delete_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    db.session.delete(ad_request)
    db.session.commit()
    flash("Ad request deleted successfully.")
    return redirect(url_for('sponsor_adrequests'))

