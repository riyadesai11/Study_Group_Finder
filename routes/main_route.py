from flask import Blueprint, request, redirect, url_for, flash, render_template
from services.authentication import get_current_user
from services.groups import (
    get_user_subject_details, get_user_groups, get_suggested_groups,
    update_user_subjects, get_all_subjects, get_user_subject_ids
)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    user_subjects = get_user_subject_details(user['id'])
    my_groups = get_user_groups(user['id'])
    suggested_groups = get_suggested_groups(user_subjects, user['id'])
        
    return render_template('dashboard.html', user=user, subjects=user_subjects, my_groups=my_groups, suggested_groups=suggested_groups)

@main_bp.route('/profile/subjects', methods=('GET', 'POST'))
def manage_subjects():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        subject_ids = request.form.getlist('subjects')
        update_user_subjects(user['id'], subject_ids)
        flash('Subjects updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
        
    all_subjects = get_all_subjects()
    user_subject_ids = get_user_subject_ids(user['id'])
    
    return render_template('manage_subjects.html', all_subjects=all_subjects, user_subject_ids=user_subject_ids)
