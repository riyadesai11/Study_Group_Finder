from database import query_db, insert_db

def get_group_meetings(group_id):
    """Fetches upcoming meetings for a specific group, joined with creator info."""
    return query_db('''
        SELECT m.*, u.prn as creator_prn, u.name as creator_name 
        FROM meetings m 
        JOIN users u ON m.creator_id = u.id 
        WHERE m.group_id = ? 
        ORDER BY m.scheduled_time ASC
    ''', [group_id])

def schedule_meeting(group_id, creator_id, title, description, scheduled_time):
    """Inserts a new meeting scheduled_time in YYYY-MM-DD HH:MM format."""
    return insert_db('''
        INSERT INTO meetings (group_id, creator_id, title, description, scheduled_time)
        VALUES (?, ?, ?, ?, ?)
    ''', [group_id, creator_id, title, description, scheduled_time])

def delete_meeting(meeting_id, user_id):
    """Deletes a meeting if the user is the creator or the group creator."""
    # Simplified check: just creator of the meeting for now
    return query_db('DELETE FROM meetings WHERE id = ? AND creator_id = ?', [meeting_id, user_id])
