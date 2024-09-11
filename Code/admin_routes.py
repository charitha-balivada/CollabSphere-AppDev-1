import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from models import db, Influencer, Sponsor, Admin, Campaign, AdRequest
from functools import wraps
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import io
import base64
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from flask import send_file


matplotlib.use('Agg')


def admin_auth_required(func):
    @wraps(func)
    def func3(*args, **kwargs):
        if 'admin_id' in session:
            return func(*args, **kwargs)
        else:
            flash("Please login first")
            return redirect(url_for('admin_login'))
    return func3


@app.route('/admin_login')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin_login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('All the fields are required')
        return redirect(url_for('admin_login'))

    admin = Admin.query.filter_by(username=username).first()

    if not admin or not check_password_hash(admin.password_hash, password):
        flash('Invalid username or password')
        return redirect(url_for('admin_login'))
    session['admin_id']=admin.id
    return redirect(url_for('admin_home'))



@app.route('/admin/home')
@admin_auth_required
def admin_home():
    # Get all campaigns that are not flagged
    all_campaigns = Campaign.query.filter_by(flagged=False).all()
    
    accepted_campaigns_tuples = db.session.query(Campaign, Sponsor, Influencer).select_from(AdRequest).\
        join(Campaign, AdRequest.campaign_id == Campaign.id).\
        join(Sponsor, Campaign.sponsor_id == Sponsor.id).\
        join(Influencer, AdRequest.influencer_id == Influencer.id).\
        filter(AdRequest.status == 'Accepted').\
        filter(Campaign.flagged == False).all()
    
    accepted_campaigns = []
    for campaign, sponsor, influencer in accepted_campaigns_tuples:
        accepted_campaigns.append({
            'campaign': campaign,
            'sponsor': sponsor,
            'influencer': influencer
        })

    return render_template('admin_home.html', accepted_campaigns=accepted_campaigns, all_campaigns=all_campaigns)



@app.route('/admin/campaign/<int:campaign_id>')
@admin_auth_required
def admin_view_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    return render_template('admin_view_campaign.html', campaign=campaign)



@app.route('/admin/users-and-campaigns', methods=['GET', 'POST'])
@admin_auth_required
def admin_users_and_campaigns():
    category_filter = request.args.get('category', '')
    type_filter = request.args.get('type', 'sponsors')  

    if type_filter == 'sponsors':
        items = Sponsor.query
        if category_filter:
            items = items.filter(Sponsor.category == category_filter)
    elif type_filter == 'influencers':
        items = Influencer.query
        if category_filter:
            items = items.filter(Influencer.category == category_filter)
    elif type_filter == 'campaigns':
        items = Campaign.query
        if category_filter:
            items = items.filter(Campaign.category == category_filter)

    items = items.all()
    
    categories = ["Fashion", "Travel", "Gaming", "Food", "Fitness", "DIY&Crafts", "Music", "Finance&Investment", "Science&Engineering", "Sports"]

    return render_template('admin_users_and_campaigns.html', items=items, type_filter=type_filter, categories=categories, selected_category=category_filter)


@app.route('/admin/sponsor/<int:sponsor_id>')
@admin_auth_required
def admin_view_sponsor(sponsor_id):
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    return render_template('admin_view_sponsor.html', sponsor=sponsor)

@app.route('/admin/influencer/<int:influencer_id>')
@admin_auth_required
def admin_view_influencer(influencer_id):
    influencer = Influencer.query.get_or_404(influencer_id)
    return render_template('admin_view_influencer.html', influencer=influencer)


@app.route('/admin/flag/<int:campaign_id>', methods=['POST'])
@admin_auth_required
def admin_flag(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    # Flag the campaign
    campaign.flagged = True
    db.session.commit()

    # Check if the campaign has any accepted influencers
    accepted_ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id, status='Accepted').all()

    if not accepted_ad_requests:
        flash(f"Campaign '{campaign.name}' has been flagged and will only appear as flagged on the sponsor's dashboard.", "warning")
    else:
        flash(f"Campaign '{campaign.name}' has been flagged and will appear as flagged on both the sponsor's and influencer's dashboards.", "warning")

    return redirect(url_for('admin_home'))  # Redirect back to admin home


def create_pie_chart(categories, values):
    # Adjust the figure size and DPI for even smaller images
    fig, ax = plt.subplots(figsize=(4, 4), dpi=80)  # Smaller figure size and lower DPI

    # Filter out categories with zero values
    non_zero_indices = [i for i, value in enumerate(values) if value > 0]
    filtered_categories = [categories[i] for i in non_zero_indices]
    filtered_values = [values[i] for i in non_zero_indices]

    if not filtered_values:  # No data to plot
        return None

    wedges, texts, autotexts = ax.pie(filtered_values, labels=filtered_categories, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired(range(len(filtered_categories))))

    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.setp(autotexts, size=6, weight="bold", color="white")  # Adjust font size
    plt.setp(texts, size=8)  # Adjust font size

    # Save it to a BytesIO object with higher quality
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0.1, dpi=100)  # Lower DPI for smaller image
    img.seek(0)

    # Encode the image to base64
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close(fig)  # Close the figure after saving

    return f"data:image/png;base64,{chart_url}"

@app.route('/admin_stats')
def admin_stats():
    # Get counts for each category for sponsors, influencers, and campaigns
    sponsor_counts = db.session.query(Sponsor.industry, db.func.count(Sponsor.id)).group_by(Sponsor.industry).all()
    influencer_counts = db.session.query(Influencer.category, db.func.count(Influencer.id)).group_by(Influencer.category).all()
    campaign_counts = db.session.query(Campaign.category, db.func.count(Campaign.id)).group_by(Campaign.category).all()

    # Define categories
    categories = ["Fashion", "Travel", "Gaming", "Food", "Fitness", "DIY&Crafts", "Music", "Finance&Investment", "Science&Engineering", "Sports"]

    # Process data for sponsors
    sponsor_data = dict(sponsor_counts)
    values_sponsors = [sponsor_data.get(cat, 0) for cat in categories]

    # Process data for influencers
    influencer_data = dict(influencer_counts)
    values_influencers = [influencer_data.get(cat, 0) for cat in categories]

    # Process data for campaigns
    campaign_data = dict(campaign_counts)
    values_campaigns = [campaign_data.get(cat, 0) for cat in categories]

    # Get counts for total number of influencers, sponsors, and campaigns
    num_influencers = sum(values_influencers)
    num_sponsors = sum(values_sponsors)
    num_campaigns = sum(values_campaigns)

    # Generate charts, only if there are non-zero values
    sponsor_chart = create_pie_chart(categories, values_sponsors)
    influencer_chart = create_pie_chart(categories, values_influencers)
    campaign_chart = create_pie_chart(categories, values_campaigns)

    return render_template('admin_stats.html',
                           num_influencers=num_influencers,
                           num_sponsors=num_sponsors,
                           num_campaigns=num_campaigns,
                           sponsor_chart=sponsor_chart if sponsor_chart else None,
                           influencer_chart=influencer_chart if influencer_chart else None,
                           campaign_chart=campaign_chart if campaign_chart else None)



@app.route('/admin_logout')
@admin_auth_required
def admin_logout():
    session.pop('admin_id')
    return redirect(url_for('admin_login'))