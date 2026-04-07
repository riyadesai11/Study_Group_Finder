from flask import Blueprint, request, redirect, url_for, flash, render_template, current_app, jsonify
from services.authentication import get_current_user
from services.groups import (
    get_all_groups, get_all_subjects, create_group as svc_create_group,
    get_group_details, get_group_members, check_is_member,
    join_group as svc_join_group, leave_group as svc_leave_group,
    is_user_in_group
)
from services.chat import get_group_messages, handle_file_upload
from services.meetings import get_group_meetings, schedule_meeting as svc_schedule_meeting
import os

groups_bp = Blueprint('groups', __name__)

@groups_bp.route('/groups')
def groups():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    all_groups = get_all_groups(user['id'])
    return render_template('groups.html', groups=all_groups)

@groups_bp.route('/group/create', methods=('GET', 'POST'))
def create_group():
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        subject_id = request.form['subject_id']
        
        group_id = svc_create_group(name, description, subject_id, user['id'])
        flash('Group created successfully!', 'success')
        return redirect(url_for('groups.group_detail', group_id=group_id))
        
    all_subjects = get_all_subjects()
    return render_template('create_group.html', subjects=all_subjects)

@groups_bp.route('/group/<int:group_id>')
def group_detail(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    group = get_group_details(group_id)
    if not group:
        flash('Group not found.', 'error')
        return redirect(url_for('groups.groups'))
        
    members = get_group_members(group_id)
    is_member = check_is_member(members, user['prn'])
    
    # Fetch messages and meetings if member
    messages = []
    meetings = []
    if is_member:
        messages = get_group_messages(group_id)
        meetings = get_group_meetings(group_id)
    
    return render_template('group_detail.html', 
                          group=group, 
                          members=members, 
                          is_member=is_member,
                          messages=messages,
                          meetings=meetings)

@groups_bp.route('/group/<int:group_id>/join', methods=('POST',))
def join_group(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    success = svc_join_group(group_id, user['id'])
    if success:
        flash('You have joined the group!', 'success')
        
    return redirect(url_for('groups.group_detail', group_id=group_id))

@groups_bp.route('/group/<int:group_id>/leave', methods=('POST',))
def leave_group(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    svc_leave_group(group_id, user['id'])
    flash('You have left the group.', 'success')
        
    return redirect(url_for('main.dashboard'))

@groups_bp.route('/group/<int:group_id>/upload', methods=('POST',))
def upload_file(group_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if not is_user_in_group(user['id'], group_id):
        return jsonify({'error': 'Access denied: You are not a member.'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    file_url = handle_file_upload(file, group_id, user['id'])
    if file_url:
        return jsonify({'success': True, 'file_url': file_url, 'file_name': file.filename})
    
    return jsonify({'error': 'File type not allowed'}), 400

@groups_bp.route('/group/<int:group_id>/schedule_meeting', methods=('POST',))
def schedule_meeting(group_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('auth.login'))
        
    title = request.form['title']
    description = request.form['description']
    date = request.form['date']
    time = request.form['time']
    
    scheduled_time = f"{date} {time}"
    svc_schedule_meeting(group_id, user['id'], title, description, scheduled_time)
    
    flash('Meeting scheduled successfully!', 'success')
    return redirect(url_for('groups.group_detail', group_id=group_id))
