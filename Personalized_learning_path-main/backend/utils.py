from datetime import datetime, timedelta
import json


def calculate_streak(activity_logs):
	"""Calculate current learning streak"""
	if not activity_logs:
		return 0
	
	# Sort by date descending
	sorted_logs = sorted(activity_logs, key=lambda x: x['date'], reverse=True)
	
	streak = 0
	current_date = datetime.now().date()
	
	for log in sorted_logs:
		log_date = log['date'] if isinstance(log['date'], datetime) else datetime.fromisoformat(log['date']).date()
		
		# Check if this log is for today or consecutive day
		expected_date = current_date - timedelta(days=streak)
		
		if log_date == expected_date:
			streak += 1
		elif log_date < expected_date:
			break  # Streak broken
	
	return streak


def generate_heatmap(activity_logs, weeks=12):
	"""Generate activity heatmap data for last N weeks"""
	heatmap_data = []
	end_date = datetime.now().date()
	start_date = end_date - timedelta(weeks=weeks)
	
	# Create dict of dates with learning minutes
	activity_dict = {}
	for log in activity_logs:
		log_date = log['date'] if isinstance(log['date'], datetime) else datetime.fromisoformat(log['date']).date()
		activity_dict[log_date] = log.get('learning_minutes', 0)
	
	# Generate data for each day in range
	current_date = start_date
	while current_date <= end_date:
		minutes = activity_dict.get(current_date, 0)
		intensity = min(minutes / 60, 4)  # 0-4 scale
		
		heatmap_data.append({
			'date': current_date.isoformat(),
			'minutes': minutes,
			'intensity': int(intensity)
		})
		
		current_date += timedelta(days=1)
	
	return heatmap_data


def check_achievements(user, progress_count, streak):
	"""Check if user has earned new achievements"""
	new_achievements = []
	
	# Define achievement criteria
	achievements_criteria = [
		{'name': 'First Steps', 'criteria': progress_count >= 1, 'xp': 50},
		{'name': '10 Topics Master', 'criteria': progress_count >= 10, 'xp': 100},
		{'name': '50 Topics Master', 'criteria': progress_count >= 50, 'xp': 500},
		{'name': 'Week Warrior', 'criteria': streak >= 7, 'xp': 200},
		{'name': 'Month Champion', 'criteria': streak >= 30, 'xp': 1000},
		{'name': 'Level 5 Achieved', 'criteria': user.current_level >= 5, 'xp': 300},
		{'name': 'Level 10 Achieved', 'criteria': user.current_level >= 10, 'xp': 500},
	]
	
	for achievement in achievements_criteria:
		if achievement['criteria']:
			new_achievements.append(achievement)
	
	return new_achievements


def calculate_xp_for_level(level):
	"""Calculate total XP needed to reach a level"""
	return level * 1000  # 1000 XP per level


def get_level_from_xp(xp):
	"""Calculate level from XP"""
	return max(1, xp // 1000)


def format_duration(minutes):
	"""Format minutes into human readable duration"""
	if minutes < 60:
		return f"{minutes} min"
	
	hours = minutes // 60
	remaining_minutes = minutes % 60
	
	if remaining_minutes == 0:
		return f"{hours} hr"
	
	return f"{hours} hr {remaining_minutes} min"
